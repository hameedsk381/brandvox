# ReputationOS AI Product Roadmap

| | |
|---|---|
| **Version** | 2.0 |
| **Last updated** | 2026-07-03 |
| **Status** | Product built and hardened; not yet validated by paying customers |
| **Next milestone** | Phase 6 — first 5 paying agencies |

This document describes the business roadmap for turning ReputationOS AI from a POC into a mature, market-ready SaaS product.

## How status is tracked

Every phase and deliverable uses one of three states. A feature is not "done" until it reaches the third.

| State | Meaning |
|---|---|
| 🔨 **Built** | The feature exists and its tests pass |
| 🔒 **Hardened** | Security, tenant isolation, and failure paths reviewed and fixed |
| 📈 **Validated** | Real customers use it and the phase's success criteria are *measured* true |

A phase is **complete only when its success criteria are measured**, not when its deliverables ship. Criteria that require customers cannot be checked before customers exist.

## 1. Product direction

ReputationOS AI is a brand reputation intelligence platform for agencies and multi-location businesses.

The product's commercial value comes from four outcomes:

- reduce manual review handling
- improve response speed and quality
- surface operational problems from customer feedback
- give managers and executives a clearer view of brand health

The roadmap is organized around readiness for revenue, retention, trust, and expansion.

## 2. Target market

Primary buyer:

- marketing agencies managing multiple client accounts

Beachhead wedge (Phase 6 focus):

- restaurant-focused agencies — highest review volume, fastest visible ROI from the reply loop

Secondary buyers (after the wedge is proven):

- multi-location businesses
- healthcare groups
- hotels
- retail brands

Why this market:

- it has recurring review volume
- it has visible ROI from faster response and better reputation
- it benefits from white-label and multi-tenant workflows
- it can expand from one location to many

## 3. Product strategy

The product should mature in this order:

1. make it sellable
2. make it reliable
3. make it sticky
4. make it secure and scalable
5. make it easy to expand commercially
6. **prove it with revenue** ← current stage

The roadmap avoids broad feature sprawl. The focus is on completing the core reputation workflow end to end. Phase 5 breadth (forecasting, customer journey, custom dashboards, copilot) shipped ahead of validation — those features are now **frozen**: no further investment until Phase 6 customer usage pulls for them, and candidates for cutting if it doesn't.

## 4. Roadmap phases

### Phase 1: Market-ready foundation — 🔒 Built & hardened, not validated

Objective:

Deliver a product that a customer can understand, try, and adopt quickly.

Key deliverables (all built):

- account creation and login
- agency/client/location tenant structure
- role-based access (7 roles with numeric privilege levels)
- onboarding flow (register → dashboard)
- Google Business Profile ingestion (OAuth flow, sync, map locations)
- manual review import
- review inbox (list, filter, search, detail pages)
- AI reply drafting (with brand voice, 2 options)
- review approval workflow (approve/reject/replace)
- dashboard with reputation score and core KPIs
- basic branding and white-label settings
- PDF/Excel/PPTX report export
- trial and pricing gating (Razorpay plans, 14-day trial, subscription gating)

Hardening completed (July 2026):

- Google OAuth CSRF protection (signed state tokens)
- refresh-token failures now fail loudly instead of storing sentinel values
- unknown star ratings skipped instead of defaulting to 5
- review edits and Google-side owner replies now sync (upsert + incremental paging)

Success criteria — **unmeasured, requires customers**:

- ⬜ a new account connects data and sees useful insights within 30 minutes (measure: median time-to-first-insight across first 10 trials)
- ⬜ users understand the product without training (measure: trials that reach first AI reply without a support contact)
- ⬜ the product can be demoed and sold consistently (measure: 3 demos delivered from the same script)

### Phase 2: Reliability and operational control — 🔒 Built & hardened, not validated

Objective:

Make the product dependable enough for active customer usage.

Key deliverables (all built):

- sync status and error visibility (per-location status/error timestamps, UI failure banners)
- retry and backfill logic (exponential backoff `min(2^failures, 24h)`, scheduler skip)
- audit logs (filterable API + UI, IP tracking)
- notification for failed syncs (Slack/Teams/Email via AlertIntegration webhooks)
- report generation (PDF, Excel, PPTX)
- reply quality controls (2-option drafts, brand voice, approval workflow)
- safer AI approval defaults (smart rules: auto_reply / approval_required / escalate / never_auto)

Hardening completed (July 2026):

- tenant-isolation audit: 13 cross-tenant access holes fixed across reviews, replies, brand voice, smart rules, competitors, alerts, SEO, tickets, dashboards, scheduled reports
- silent mock-data fallbacks removed from production paths (gated behind `DEMO_MODE`)
- scheduler duplicate-run protection (PostgreSQL advisory lock) for multi-replica deployments
- Alembic made the sole schema authority in production

Success criteria — **partially measurable today**:

- ✅ data sync issues are visible to administrators (status API + UI banners + webhook notifications exist and are tested)
- ⬜ support can diagnose issues quickly (measure: median time-to-diagnosis on first 10 real support tickets)
- ⬜ the workflow remains stable under normal business use (measure: 30 days of real-tenant syncs with <1% failed-sync rate)

### Phase 3: Retention and daily value — 🔨 Built, not validated

Objective:

Make the product part of a customer's regular operating rhythm.

Key deliverables (all built):

- sentiment deep dive (analytics page, emotion breakdown, source/location distribution)
- topic and root-cause summaries
- competitor tracking (CRUD, SWOT analysis via AI)
- alerts and escalation workflows (crisis detection, severity levels, webhook dispatch)
- executive summaries and scheduled reports (5-min scheduler, PDF/Excel/PPTX cadence)
- saved views and filters (persisted presets)
- AI recommendations tied to business actions

Success criteria — **unmeasured, requires customers**:

- ⬜ teams use the product weekly, not only during incidents (measure: weekly active accounts / total accounts ≥ 60%)
- ⬜ managers extract operational insight without reading every review (measure: analytics page views per account per week)
- ⬜ the product is part of reporting rhythms (measure: % of accounts with an active scheduled report)

### Phase 4: Trust, compliance, and enterprise readiness — 🔒 Built & hardened, not validated

Objective:

Make the product credible for larger customers and more formal procurement.

Key deliverables (all built):

- MFA for administrative users (TOTP, QR provisioning)
- password and session policies (complexity rules, strength meter, JWT iat/jti, login rate limiting)
- account recovery (secure single-use reset tokens, 1-hour expiry)
- GDPR export and delete controls
- monitoring and alerting (scheduler health endpoint, crisis webhooks)
- logging and error tracking (audit logs, request IDs, exception handlers)
- security and privacy documentation
- retention policy controls (90-day audit log purge)

Hardening completed (July 2026):

- Google OAuth tokens and client secrets encrypted at rest (Fernet, `ENCRYPTION_KEY`)
- production startup guards: refuses to boot with default JWT secret, missing encryption key, or `DEMO_MODE` enabled

Open items:

- 🔨 backup and restore process — scripts (`scripts/backup_db.sh`, `scripts/restore_db.sh`) and `docs/ops-runbook.md` written 2026-07-05; **first restore drill still pending** (drill log in the runbook)
- ⬜ external security review or pentest (SOC 2 "posture" is self-assessed until a third party looks)

Success criteria — **unmeasured, requires a real procurement process**:

- ⬜ pass a customer security questionnaire without exceptions (measure: first completed questionnaire)
- ⬜ answer procurement questions confidently (measure: first enterprise deal reaching security review stage)

### Phase 5: Expansion and differentiation — 🔨 Built, FROZEN pending validation

Objective:

Move from useful tool to strategic platform.

> **Status note:** these features shipped ahead of core-workflow validation, against this roadmap's own sequencing advice. They are frozen — no new investment — until Phase 6 usage data shows which ones customers actually pull for. Features with no usage after the first 5 paying customers are candidates for removal from the sold package (kept in code, hidden from UI).

Built:

- forecasting (AI trend prediction, 24h cache)
- crisis detection (AI + keyword fallback, severity categories)
- customer journey intelligence (profiles, touchpoints, tickets, funnel)
- competitor benchmarking (comparative analytics, SWOT)
- public API access (SHA-256 hashed keys, scoped permissions)
- generic webhook system (HMAC signing, retry with backoff, delivery history)
- custom dashboards (saved layouts and widgets)
- executive copilot (AI chat agent with tool use)

Success criteria — **deferred to post-Phase 6**:

- ⬜ customers see value beyond review management (measure: feature usage among paying accounts)
- ⬜ upsell opportunities exist (measure: first expansion revenue event)

### Phase 6: First revenue — ⬜ NOT STARTED ← current focus

Objective:

Prove the product with paying customers in one wedge market. Everything else on this roadmap is now subordinate to this phase.

Goal:

**5 paying agencies within 90 days of go-to-market start**, in the restaurant-agency wedge.

Key deliverables:

- ⬜ pricing finalized and published (Razorpay keys configured in production — currently empty)
- 🔨 production deployment config (`docker-compose.prod.yml`: prod guards, migrations-on-boot, no dev mounts) — **actual deployment to a real domain still pending**
- ⬜ Google Business Profile API production access approved (quota-request steps documented in `docs/onboarding-runbook.md` §0 — each Google Cloud project starts with quota 0 until approved; longest lead time, start first)
- 🔨 onboarding runbook for the first 10 trials — `docs/onboarding-runbook.md` (2026-07-05); validate against real onboardings
- 🔨 demo script + demo tenant — `docs/demo-script.md` keyed to seeded Stellar Digital / Tasty Burger data; validate by delivering 3 demos from it
- ⬜ 10 discovery conversations with restaurant-focused agencies
- ⬜ 3 design-partner trials at discounted pricing in exchange for weekly feedback
- 🔨 activation KPIs instrumented (2026-07-05): `Agency.first_synced_at` / `first_ai_reply_at` stamped automatically; `GET /api/analytics/activation` returns time-to-first-sync and time-to-first-AI-reply (migration `004`)

Success criteria:

- ⬜ 5 agencies paying real money
- ⬜ ≥ 60% of paying accounts active weekly
- ⬜ at least one account expands (adds locations or upgrades plan)
- ⬜ churn decisions understood (exit interview for every cancelled trial)

Exit condition: when these are met, revisit Phases 3–5 success criteria with real data and unfreeze the Phase 5 features that customers pulled for.

## 5. Release order (all shipped; validation pending)

The build sequence prioritized immediate value over breadth and is done:

1. Google review ingestion
2. review inbox and filters
3. AI reply drafting and approval
4. sentiment and topic analysis
5. dashboard and reporting
6. branding and white-label controls
7. billing and trial management
8. alerts and escalation
9. competitor intelligence
10. forecasting and advanced AI features

The release order for what remains is Phase 6, in the order listed there.

## 6. KPI scoreboard

Track the product by business outcomes, not feature completion. Honest current values — zeros create urgency; an unmeasured list creates nothing.

| KPI | Current value (2026-07-03) | Phase 6 target |
|---|---|---|
| Paying accounts | 0 | 5 |
| Trial accounts (real) | 0 (1 internal test tenant) | 10 |
| Demo-to-trial conversion | not measured | track from first demo |
| Trial-to-paid conversion | not measured | ≥ 30% |
| Time to first value (connect → first insight) | not instrumented | < 30 min, instrumented |
| First AI reply generated per trial | not instrumented | ≥ 80% of trials |
| Weekly active accounts | 0 | ≥ 60% of paying |
| Review response rate (per account) | not measured | baseline, then +20% |
| Scheduled-report adoption | not measured | ≥ 50% of paying accounts |
| Expansion revenue events | 0 | ≥ 1 |
| Churned trials with exit interview | n/a | 100% |

Update this table monthly. A KPI that stays "not measured" for two updates gets instrumented or deleted.

## 7. What to defer

These items should not delay market entry:

- multi-AI-provider support
- complex enterprise procurement features
- heavy infrastructure scaling
- too many integrations at once
- **any further Phase 5 feature work** (frozen until pulled by paying customers)
- broad industry customization before the restaurant-agency wedge is proven

## 8. Risks

Main risks:

- the product became broad before it was validated (this already happened — Phase 5 shipped before Phase 1 was measured; the freeze is the correction)
- AI output is not trusted by users
- Google integration reliability at real quota levels (GBP quota approval per agency is an onboarding dependency, not a given)
- onboarding takes too long
- pricing is not matched to value

How to reduce them:

- sell the narrow core (ingest → reply → report); treat frozen features as demo garnish, not the pitch
- require human approval for risky AI actions (default smart rules already do this)
- make sync status visible; monitor failed-sync rate as a first-class metric
- optimize and *measure* time to first value
- validate pricing in the 10 discovery conversations before publishing it

## 9. Definition of market-ready

ReputationOS AI is market-ready when it can:

- onboard a customer without heavy manual setup
- ingest real review data reliably **at production Google quota**
- help the user respond faster and better
- show useful business insight from customer feedback
- support billing, permissions, and branding
- retain users because it fits their operating workflow

The engineering for all six exists. **Market-ready is claimed only when a stranger's money confirms it** — that is Phase 6's job.

## 10. Practical summary

What is true today:

- the core workflow (multi-tenant structure, ingestion, AI replies, analytics, reporting, branding, billing scaffolding) is built and, as of July 2026, security-hardened
- nothing has been validated by a paying customer, and most success criteria in this document cannot be honestly checked until one exists

The minimum credible path from here is not more features. It is: close the Phase 4 open items, stand up production, and run Phase 6 until five agencies pay.

---

## Current status summary

| Phase | State | Evidence |
|---|---|---|
| Phase 1 — Market-ready foundation | 🔒 Built & hardened | Test suite green; July 2026 security audit fixes; criteria unmeasured |
| Phase 2 — Reliability and operational control | 🔒 Built & hardened | Tenant-isolation audit, DEMO_MODE gating, scheduler lock; no real-tenant uptime data |
| Phase 3 — Retention and daily value | 🔨 Built | Features exist; zero usage data |
| Phase 4 — Trust, compliance, enterprise | 🔒 Built & hardened (2 open items) | Encryption at rest, startup guards; backup process and external review outstanding |
| Phase 5 — Expansion and differentiation | 🔨 Built, frozen | No investment until customer pull |
| Phase 6 — First revenue | ⬜ Not started | 0 paying customers |

**Change log**
- v2.0 (2026-07-03): Re-baselined statuses to built/hardened/validated; success criteria made measurable and unchecked where unmeasured; Phase 5 frozen; Phase 6 (first revenue) added; KPI scoreboard with current values; versioning added.
- v1.x: Original roadmap; marked all phases complete on feature existence.
