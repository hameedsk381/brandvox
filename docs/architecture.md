# ReputationOS AI — Architecture

> Canonical structural reference. Last updated: **2026-07-05**.
> Companion docs: [knowledge-graph.md](knowledge-graph.md) (detailed file map + change log),
> [product.md](product.md) (feature reference), [product-roadmap.md](product-roadmap.md) (status authority),
> [ops-runbook.md](ops-runbook.md) (deploy/backup/restore), [onboarding-runbook.md](onboarding-runbook.md) (pilot playbook).

## 1. System overview

```
┌───────────────────────┐     HTTP/REST      ┌───────────────────────┐
│  Frontend (Next.js 15)│ ◄────────────────► │  Backend (FastAPI)    │
│  React 19 · TS ·      │   JWT / X-API-Key  │  Python 3.12 · async  │
│  Zustand · TanStack   │                    │  SQLAlchemy 2 ·       │
│  Query · shadcn/ui    │                    │  Pydantic 2 ·         │
│  :3000                │                    │  APScheduler   :8000  │
└───────────────────────┘                    └──────────┬────────────┘
                                                        │ asyncpg
                                             ┌──────────▼────────────┐
                                             │  PostgreSQL 16        │
                                             │  Alembic migrations   │
                                             └──────────┬────────────┘
                                                        │
                     ┌──────────────────────────────────┼──────────────────┐
                     ▼                    ▼             ▼                  ▼
             Google Business        Groq LLM       Razorpay          Twilio/SendGrid
             Profile APIs           (gpt-oss-120b) (billing +        (campaign SMS /
             (OAuth, reviews,                       signed webhooks)  email; optional)
              reply publish)
```

Single deployable unit via Docker Compose. No message queue, no cache tier, no
separate worker — APScheduler runs inside the API process, guarded by a
PostgreSQL advisory lock so extra replicas don't duplicate jobs. This is a
deliberate pilot-scale choice; revisit only when real load demands it.

## 2. Multi-tenant data model

```
Agency ──1:N── Client ──1:N── Location ──1:N── Review ──1:1── SentimentResult
  │              │               │                │              (model column marks
  │              │               │                └─1:N─ ReviewReply, TopicResult
  │              │               │                        CrisisAlert)
  │              │               ├── SmartRule, Competitor(+CompetitorReview),
  │              │               │   ReviewCampaign, ReputationScore
  │              └── GoogleIntegration (OAuth tokens, sync state)
  │              └── BrandVoiceProfile
  └── BrandingConfig, User(7 roles), WebhookEndpoint, APIKey,
      ScheduledReport, subscription fields, activation KPIs
```

- **Agency** is the paying customer (a marketing agency). Billing, branding,
  users, webhooks, and activation KPIs (`first_synced_at`, `first_ai_reply_at`)
  live here.
- **Client** is a business the agency manages; holds the Google integration
  and brand voice.
- **Location** maps 1:1 to a Google Business Profile location
  (`google_location_id`) and owns reviews and automation rules.
- Isolation is enforced in the API layer via shared helpers
  (`check_review_access`, `check_location_access`) — audited July 2026,
  regression-tested in `tests/test_tenant_isolation.py`.

## 3. Core flow: review lifecycle

```
GBP OAuth connect (signed 10-min JWT state, CSRF-proof)
  → map Location ↔ GBP location
  → sync (hourly scheduled + manual): incremental by updateTime with 1-day
    overlap; upserts edits; mirrors owner replies posted on Google; skips
    unknown star ratings; per-location 120s timeout; exponential backoff
    min(2^failures, 24h) on failure — timeouts count as failures
  → per NEW review: sentiment + topics (Groq, keyword fallback tagged in
    SentimentResult.model) → smart rules → crisis detection
      • backfill guard: reviews older than the Google connection NEVER
        trigger smart rules or crisis alerts (first sync imports history)
  → smart rules: explicit per-location rating-range rules only;
      DEFAULT WITH NO RULE = drafts for approval (1-2★ escalate).
      Auto-publish is opt-in, never a default.
  → reply: 2 AI drafts (brand voice) → human approve/edit → publish to GBP
      (≤4096 chars enforced; template fallback disabled in production)
  → analytics: reputation score (0-100 weighted; None when no reviews),
      dashboards, white-label PDF/Excel/PPTX reports emailed on schedule
```

## 4. Background jobs (APScheduler + pg advisory lock)

| Job | Interval | Notes |
|---|---|---|
| `sync_google_reviews` | 1h | Skips integrations in backoff; tz-aware comparisons |
| `process_scheduled_reports` | 5min | Generates AND emails to recipients; `last_sent_at` only on delivered |
| `retry_webhook_deliveries` | 5min | Updates the original delivery row; max 3 attempts (60/300/900s) |
| `cleanup_old_audit_logs` | daily | Bulk DELETE past retention (default 90 days) |

## 5. Security architecture

| Layer | Mechanism |
|---|---|
| AuthN | JWT (HS256, 24h) + optional TOTP MFA; API keys (SHA-256 hashed, `rpk_` prefix) |
| AuthZ | 7 roles with numeric privilege levels; tenant-scope checks on every by-ID endpoint |
| OAuth CSRF | `state` = signed 10-min JWT (client_id + nonce) |
| Tokens at rest | Fernet `EncryptedToken` column type (Google tokens, OAuth client secrets); `ENCRYPTION_KEY` required in production |
| Billing | Razorpay webhook requires HMAC-SHA256 over the raw body (`RAZORPAY_WEBHOOK_SECRET`); unsigned = 400. Subscription state changes: verified webhook or super_admin only |
| Startup guards | Production refuses to boot with default `JWT_SECRET`, missing `ENCRYPTION_KEY`, or `DEMO_MODE=true` |
| Schema | Alembic is the sole migration path in production (`create_all` skipped) |

## 6. AI integrity invariants

These are product decisions, not implementation details — do not regress them:

1. **No silent fake data in production.** Mock replies, mock reviews, placeholder
   SWOTs, and fabricated scores are gated behind `DEMO_MODE`/development.
   Production failures surface as errors or empty results, never as invented output.
2. **Degradation is recorded.** `SentimentResult.model` distinguishes
   `groq:*` from `keyword_fallback`.
3. **Sample data is labeled end-to-end.** `competitor_reviews.source`,
   `is_sample_data` API flag, UI banner, `[Sample data]` prefix in stored summaries.
4. **Nothing auto-publishes without an explicit rule.** The no-rule default is
   human approval; historical backfill never triggers automation.
5. **The review funnel does not gate.** Every rating gets the identical next
   step (Google policy / FTC review rule). Rating-based routing is prohibited.

## 7. Deployment

- **Dev**: `docker compose up` — hot reload, source mounts, Dockerfile `dev`
  target (includes pytest).
- **Prod**: `docker compose -f docker-compose.prod.yml up -d` — `base` target,
  no mounts, `alembic upgrade head` before serve, restart policies, postgres
  not exposed on the host. Required env fails fast (`:?` expansion).
- **Backups**: nightly `scripts/backup_db.sh` (pg_dump -Fc, 14-day rotation),
  restore via `scripts/restore_db.sh`; drill procedure in ops-runbook.
- **CI**: GitHub Actions (`.github/workflows/ci.yml`) runs the backend pytest
  suite (SQLite in-memory, no services) on every push/PR.
- **Tests**: `docker compose run --rm --no-deps backend python -m pytest tests/ -q`
  — 86 tests as of 2026-07-05.

## 8. Evolution triggers (deliberately deferred)

External architecture review (2026-07-05) scored this design ~9/10 for MVP →
~1-2k customers and flagged the gaps below. They are **intentionally deferred**
— adopting them pre-revenue would repeat the Phase 5 mistake (breadth before
validation). Each has an explicit adoption trigger; before the trigger fires,
building it is waste.

| Capability | Adopt when | Likely shape |
|---|---|---|
| Dedicated job queue (retries, DLQ, monitoring) | Jobs need per-task retry state, or a second app instance is real | Celery/Temporal; APScheduler jobs are already isolated functions, migration is mechanical |
| Event-driven pipeline | A third consumer of the review lifecycle appears (today: sync loop is the only producer) | Postgres LISTEN/NOTIFY or outbox table first; broker only after that strains |
| Observability stack | First paying customer (error tracking) → first enterprise deal (tracing) | Sentry first — cheapest, highest value; request IDs + audit logs already exist as the seam |
| AI orchestration (policy check, tone eval, quality score stages) | Customers reject >X% of AI drafts, measured — not before | Extend the existing pipeline functions; no framework until ≥3 stages exist |
| AI audit trail (prompt/model versioning) | First enterprise security questionnaire | Embryo exists: `SentimentResult.model`, `ReviewReply.generated_by/approved_by`; add prompt_version column |
| Vector search / memory | A feature needs semantic retrieval over review history (e.g. "similar past complaints") | pgvector inside the existing Postgres before any dedicated vector DB |
| Multi-provider LLM / fallback | Groq outage actually costs a customer, or a customer demands model choice | Provider interface around `groq_client.py`; keyword fallbacks already isolate the blast radius |
| Redis / caching | Rate limiting or session state outgrows in-process, or an AI result is recomputed measurably often | Forecasting already demonstrates the pattern (24h DB-backed cache) |
| Feature flags | More than ~3 pilot tenants need staged rollouts | Start with a JSON column on Agency (`settings` exists); LaunchDarkly-class tooling much later |

Resilience notes as of today: LLM calls retry 3× with backoff and degrade to
*tagged* fallbacks (never silent); sync has per-location timeouts + exponential
backoff; webhooks retry 3× with capped delays and exhaust cleanly; billing
webhooks are idempotent by construction (setting the same plan twice is a no-op).
The known weak spot is a hard Groq outage during a large backfill — acceptable
at pilot scale because sync itself never blocks on AI.

## 9. Known constraints

- Google GBP APIs start at **quota 0** per Google Cloud project until Google
  approves access (weeks of lead time) — see onboarding-runbook §0.
- Groq free tier (30 RPM) will rate-limit large first-sync backfills; sentiment
  falls back to tagged keyword analysis rather than blocking sync.
- Single-box architecture: the scheduler advisory lock allows replicas but the
  system is designed and tested for one instance.
- Frontend `next.config.ts` currently sets `ignoreBuildErrors: true` (3
  pre-existing landing-page type errors); fix and flip to false.
