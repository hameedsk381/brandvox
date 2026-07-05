# BrandVox / ReputationOS Knowledge Graph

> **Project:** AI-Powered Brand Reputation Intelligence Platform
> **Stack:** FastAPI + Next.js 15 + PostgreSQL 16 + Docker
> **Last updated:** 2026-07-03 (post security-hardening pass)
> **Status authority:** `docs/product-roadmap.md` v2.0 — this file describes architecture, not readiness

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BRANDVOX (ReputationOS)                           │
│                    AI-Powered Brand Reputation Platform                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
           ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
           │   FRONTEND   │    │   BACKEND    │    │  DATABASE    │
           │  (Next.js 15)│    │  (FastAPI)   │    │  (PostgreSQL)│
           │  Port: 3000  │    │  Port: 8000  │    │  Port: 5432  │
           └──────────────┘    └──────────────┘    └──────────────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       ▼
                          ┌──────────────────────┐
                          │   EXTERNAL SERVICES  │
                          │  Google Business API │
                          │  Groq AI API         │
                          │  Razorpay Billing    │
                          │  Webhook Endpoints   │
                          └──────────────────────┘
```

---

## 📦 Project Structure

```
brandvox/
├── backend/                          # FastAPI Application
│   ├── app/
│   │   ├── api/                      # 20+ API Routers
│   │   │   ├── auth.py               # Authentication (JWT, MFA)
│   │   │   ├── google_auth.py        # Google OAuth & GBP Integration
│   │   │   ├── reviews.py            # Review CRUD & AI Replies
│   │   │   ├── replies.py            # Reply Management
│   │   │   ├── analytics.py          # Dashboard Analytics
│   │   │   ├── tenants.py            # Multi-tenant (Agency/Client)
│   │   │   ├── competitors.py        # Competitor Analysis
│   │   │   ├── alerts.py             # Crisis Alerts
│   │   │   ├── forecasting.py        # Review Volume Forecasting
│   │   │   ├── reports.py            # Report Generation (PDF/CSV/PPTX)
│   │   │   ├── scheduled_reports.py  # Automated Reports
│   │   │   ├── billing.py            # Razorpay Integration
│   │   │   ├── branding.py           # White-label Branding
│   │   │   ├── brand_voice.py        # AI Brand Voice Profiles
│   │   │   ├── smart_rules.py        # Auto-reply Rules Engine
│   │   │   ├── campaigns.py          # Review Campaigns
│   │   │   ├── chat.py               # AI Chatbot Widget
│   │   │   ├── customer_journey.py   # Customer Journey Mapping
│   │   │   ├── seo.py                # SEO Insights
│   │   │   ├── dashboards.py         # Custom Dashboards
│   │   │   ├── users.py              # User Management
│   │   │   ├── webhooks.py           # Webhook Delivery
│   │   │   ├── api_keys.py           # API Key Management
│   │   │   ├── audit.py              # Audit Logging
│   │   │   └── health.py             # Health Checks
│   │   ├── core/
│   │   │   ├── auth.py               # JWT Token Handling
│   │   │   ├── crypto.py             # Fernet EncryptedToken column type (tokens at rest)
│   │   │   ├── dependencies.py       # Auth & Permission Dependencies (incl. check_review_access)
│   │   │   ├── permissions.py        # Role-based Access Control
│   │   │   └── scheduler.py          # Background Jobs (APScheduler + pg advisory lock)
│   │   ├── models/                   # 23 SQLAlchemy Models
│   │   │   ├── tenant.py             # Agency, Client, Location
│   │   │   ├── integration.py        # GoogleIntegration
│   │   │   ├── review.py             # Review, ReviewReply
│   │   │   ├── user.py               # User (with MFA)
│   │   │   ├── sentiment.py          # SentimentResult, TopicResult
│   │   │   ├── analytics.py          # ReputationScore, Dashboard
│   │   │   ├── competitor.py         # Competitor, CompetitorAnalysis
│   │   │   ├── alert.py              # Alert, AlertIntegration
│   │   │   ├── forecast.py           # ForecastPoint
│   │   │   ├── campaign.py           # ReviewCampaign
│   │   │   ├── scheduled_report.py   # ScheduledReport
│   │   │   ├── branding.py           # BrandingConfig, BrandVoiceProfile
│   │   │   ├── smart_rules.py        # SmartRule
│   │   │   ├── chat.py               # ChatSession, ChatMessage
│   │   │   ├── webhook.py            # Webhook, WebhookDelivery
│   │   │   ├── api_key.py            # APIKey
│   │   │   ├── audit.py              # AuditLog
│   │   │   └── seo.py                # SEOInsight
│   │   ├── schemas/                  # 20+ Pydantic Schemas
│   │   ├── services/                 # 16 Business Logic Services
│   │   │   ├── google_integration_service.py  # GBP Sync Core
│   │   │   ├── review_service.py
│   │   │   ├── reply_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── sentiment_service.py
│   │   │   ├── intelligence_service.py
│   │   │   ├── competitor_service.py
│   │   │   ├── forecasting_service.py
│   │   │   ├── campaign_service.py
│   │   │   ├── branding_service.py
│   │   │   ├── billing_service.py
│   │   │   ├── webhook_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── alert_service.py
│   │   │   ├── api_key_service.py
│   │   │   └── report_service.py
│   │   ├── ai/                       # AI Pipeline
│   │   │   ├── groq_client.py        # Groq API Wrapper
│   │   │   ├── sentiment.py          # Sentiment Analysis
│   │   │   ├── topic_extraction.py   # Topic Modeling
│   │   │   ├── review_reply.py       # AI Reply Generation
│   │   │   ├── agent.py              # AI Agent Orchestration
│   │   │   └── prompts.py            # Prompt Templates
│   │   ├── database.py               # Async SQLAlchemy Setup
│   │   ├── config.py                 # Settings (Pydantic Settings)
│   │   ├── seed/
│   │   │   └── seed_data.py          # Database Seeder
│   │   └── main.py                   # FastAPI App Entry Point
│   ├── tests/                        # 14 Test Modules (62 tests, all passing)
│   │   ├── test_google_integration_e2e.py
│   │   ├── test_google_integration_observability.py
│   │   ├── test_tenant_isolation.py  # Cross-tenant 403 regression tests
│   │   ├── test_auth.py
│   │   ├── test_reviews.py
│   │   ├── test_replies.py
│   │   ├── test_analytics.py
│   │   ├── test_competitors.py
│   │   ├── test_alerts.py
│   │   ├── test_forecasting.py
│   │   ├── test_reliability.py       # Incl. review upsert / rating-skip / reply-mirror tests
│   │   ├── test_reports.py
│   │   ├── test_audit.py
│   │   └── test_ai.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                         # Next.js 15 Application
│   ├── src/
│   │   ├── app/                      # App Router Pages
│   │   │   ├── dashboard/            # Protected Dashboard Routes
│   │   │   │   ├── integrations/     # Google Business Profile Setup
│   │   │   │   ├── reviews/          # Review Management UI
│   │   │   │   ├── analytics/        # Analytics & Forecasting
│   │   │   │   ├── competitors/      # Competitor Analysis
│   │   │   │   ├── alerts/           # Crisis Alerts
│   │   │   │   ├── settings/         # 8 Settings Sub-pages
│   │   │   │   ├── review-campaigns/ # Campaign Management
│   │   │   │   ├── seo/              # SEO Insights
│   │   │   │   ├── customer-journey/ # Journey Mapping
│   │   │   │   ├── custom-dashboards/# Dashboard Builder
│   │   │   │   ├── reports/          # Report Generation
│   │   │   │   └── copilot/          # AI Assistant
│   │   │   ├── login/                # Auth Pages
│   │   │   ├── register/
│   │   │   ├── forgot-password/
│   │   │   ├── reset-password/
│   │   │   └── review-funnel/        # Public Review Collection
│   │   ├── components/
│   │   │   ├── ui/                   # 20+ shadcn/ui Components
│   │   │   ├── dashboard/            # Dashboard Widgets
│   │   │   ├── reviews/              # Review Cards, Filters, AI Reply
│   │   │   ├── branding/             # Logo, Color, Preview
│   │   │   ├── analytics/            # Charts (Sentiment, Volume, etc.)
│   │   │   ├── layout/               # Sidebar, Topbar, Tenant Switcher
│   │   │   ├── chat/                 # Customer Widget
│   │   │   └── landing/              # Marketing Components
│   │   ├── lib/
│   │   │   ├── api.ts                # Axios Client + All API Services
│   │   │   ├── constants.ts
│   │   │   └── utils.ts
│   │   ├── hooks/
│   │   │   ├── use-reviews.ts        # React Query for Reviews
│   │   │   ├── use-tenant.ts         # Client/Location Context
│   │   │   ├── use-branding.ts
│   │   │   └── use-auth.ts
│   │   ├── stores/
│   │   │   ├── auth-store.ts         # Zustand Auth State
│   │   │   ├── tenant-store.ts       # Client/Location Selection
│   │   │   ├── filter-store.ts       # Review Filters
│   │   │   ├── branding-store.ts
│   │   │   └── chat-store.ts
│   │   └── types/index.ts            # TypeScript Interfaces
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
│
├── docker-compose.yml                # Multi-container Orchestration
├── .env                              # Environment Variables
├── .env.example
├── README.md
└── docs/                             # Product Documentation
```

---

## 🔐 Authentication & Authorization Flow

```
                    ┌───────────────┐
                    │  User Login   │
                    │  /api/auth/   │
                    │  login        │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  JWT Token    │
                    │  (HS256, 24h) │
                    └───────┬───────┘
                            │
                            ▼
                    ┌─────────────────────────────┐
                    │   REQUEST ╥ RESPONSE        │
                    │  Interceptor║ Interceptor    │
                    │  Add Bearer ║ 401 → Logout  │
                    └─────────────╫───────────────┘
                                  ║
                                  ▼
                    ┌─────────────────────────────┐
                    │      BACKEND DEPENDENCIES   │
                    │  get_current_user (JWT)     │
                    │  get_current_active_user    │
                    │  SubscriptionRequired       │
                    └─────────────┬───────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │   ROLE-BASED ACCESS CONTROL │
                    │  super_admin (full access)  │
                    │  agency_admin (agency scope)│
                    │  client_admin (client scope)│
                    │  marketing_manager          │
                    │  customer_support           │
                    │  branch_manager             │
                    └─────────────────────────────┘
```

---

## 🏢 Multi-Tenant Data Model

```
┌──────────────┐
│    AGENCY    │  ───  Google OAuth creds, Razorpay, Subscription
│  (agencies)  │
└──────┬───────┘
       │ 1:N
       ▼
┌──────────────┐
│    CLIENT    │  ───  Business managed by agency
│  (clients)   │
└──────┬───────┘
       │ 1:N
       ▼
┌──────────────┐
│   LOCATION   │  ───  Physical location (maps to GBP)
│ (locations)  │        google_location_id → GBP mapping
└──────┬───────┘
       │
       ├──────────────────┬──────────────────┬──────────────────┐
       ▼                  ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    REVIEW    │  │  SMART RULE  │  │  COMPETITOR  │  │   CAMPAIGN   │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🔄 Google Business Profile Integration Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FRONTEND  │     │   BACKEND   │     │   GOOGLE    │     │  DATABASE   │
│             │     │             │     │   APIs      │     │             │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │  1. GET /auth-url │                   │                   │
       │──────────────────>│                   │                   │
       │<──────────────────│                   │                   │
       │  2. Redirect to   │                   │                   │
       │     Google OAuth  │                   │                   │
       │                   │                   │                   │
       │  3. User consents │                   │                   │
       │                   │                   │                   │
       │  4. POST /callback│                   │                   │
       │     (code, state) │                   │                   │
       │──────────────────>│  5. Exchange code │                   │
       │                   │     for tokens    │                   │
       │                   │──────────────────>│                   │
       │                   │<──────────────────│                   │
       │                   │  6. Save tokens   │                   │
       │                   │──────────────────────────────────────>│
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │  7. GET /locations│                   │                   │
       │──────────────────>│  8. Fetch accounts │                  │
       │                   │──────────────────>│                   │
       │                   │  9. Fetch locs    │                   │
       │                   │──────────────────>│                   │
       │                   │<──────────────────│                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │ 10. POST /map-loc │                   │                   │
       │──────────────────>│ 11. Update loc    │                   │
       │                   │──────────────────────────────────────>│
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │ 12. POST /sync    │                   │                   │
       │──────────────────>│ 13. Fetch reviews │                   │
       │                   │──────────────────>│                   │
       │                   │<──────────────────│                   │
       │                   │ 14. Store + AI    │                   │
       │                   │──────────────────────────────────────>│
       │<──────────────────│                   │                   │
```

**Flow hardening (July 2026):**

- OAuth `state` is a signed 10-min JWT (client_id + nonce) — CSRF-protected; raw client_id is rejected
- Missing refresh token on first connect fails loudly (no sentinel values stored)
- Sync **upserts**: review edits on Google update the local copy (sentiment re-analyzed, smart rules NOT re-run)
- Owner replies posted directly on Google are mirrored as `ReviewReply(generated_by="google_sync")`
- Incremental paging: sync stops at reviews older than last sync minus 1-day overlap (GBP quota protection)
- Unknown star ratings are **skipped**, never defaulted
- Google API failures raise errors; mock fallback only when `DEMO_MODE=true` (explicit `test-client-id` test mode unaffected)
- **Workflow review fixes (2026-07-05):** smart-rule default is now approval-only (auto-reply requires an explicit rule); first-sync backlog (reviews older than the Google connection) never triggers smart rules or crisis alerts; sync timeouts count toward backoff; scheduled reports are emailed to recipients (`last_sent_at` only stamped on successful delivery); webhook retries update the original delivery row instead of duplicating sends; hourly sync no longer crashes on tenants in backoff (naive/aware datetime fix)
- **Product-review fixes (2026-07-05):** review funnel de-gated — every rating now gets the identical next step (public Google review option + optional private feedback); rating-based routing removed as prohibited review gating (Google policy / FTC review rule); hardcoded fallback Google review URL removed. Competitor sample data labeled end-to-end: `competitor_reviews.source` column (migration `006`), `is_sample_data` flag on analytics API, amber banner in the competitors UI, `[Sample data]` prefix stored in SWOT summaries, and the fabricated heuristic SWOT fallback now refuses to run in production.
- **Core-logic review fixes (2026-07-05):** Razorpay webhook now requires a valid raw-body HMAC signature (`RAZORPAY_WEBHOOK_SECRET`) — unsigned/forged events rejected; `PATCH /billing/update` restricted to super_admin (agency admins can no longer self-upgrade); free/mock plan activation moved server-side into checkout (mock only outside production); reputation score fixed to a real 0–100 (was 10× inflated) and returns `None` with no reviews instead of a fabricated 75; `review_growth` computed from real 30-day windows (was hardcoded 14.5); AI reply template fallback disabled in production (API failure → empty → manual queue); sentiment results carry a `model` column (`groq:*` vs `keyword_fallback`, migration `005`); replies validated against Google's 4096-char limit; crisis keyword "sick" replaced with specific phrases
- Note: each agency's Google Cloud project has **GBP API quota 0 until Google approves access** — onboarding dependency

---

## 🤖 AI Processing Pipeline

```
                    ┌─────────────────────┐
                    │   NEW REVIEW        │
                    │   (via Sync/API)    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  SENTIMENT ANALYSIS │
                    │  - Polarity (±)     │
                    │  - Score (-1 to +1) │
                    │  - Emotions         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  TOPIC EXTRACTION   │
                    │  Service, Food,     │
                    │  Staff, Price, etc. │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  SMART RULES CHECK  │
                    │  Auto-reply /       │
                    │  Approval / Escalate│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  AI REPLY GENERATION│
                    │  (Groq: gpt-oss-120b)│
                    │  Brand Voice context│
                    │  Temp: 0.7 replies, │
                    │  0.1 analysis       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  PUBLISH TO GBP     │
                    │  (or Queue for      │
                    │   Approval)         │
                    └─────────────────────┘
```

---

## ⚙️ Background Scheduler Jobs

| Job | Interval | Description |
|-----|----------|-------------|
| `sync_google_reviews` | Every 1 hour | Fetch new/edited reviews for all GBP-mapped locations (incremental) |
| `process_scheduled_reports` | Every 5 min | Generate due PDF/Excel/PPTX reports |
| `cleanup_old_audit_logs` | Daily | Purge logs older than 90 days |
| `retry_webhook_deliveries` | Every 5 min | Retry failed webhook deliveries |

Only one process runs jobs: startup takes a **PostgreSQL advisory lock** (`pg_try_advisory_lock`), so extra uvicorn workers/replicas skip scheduler startup. `ENABLE_SCHEDULER=false` disables it explicitly.

---

## 🔑 Key Environment Variables

| Variable | Status | Notes |
|----------|--------|-------|
| `DATABASE_URL` | ✅ Configured | PostgreSQL + asyncpg |
| `JWT_SECRET` | ⚠️ Default | **Startup refuses to boot in production with default** |
| `ENVIRONMENT` | `development` | Set `production` to enforce startup security guards |
| `ENCRYPTION_KEY` | ⚠️ Unset | Fernet key for OAuth tokens at rest; required in production (dev derives from JWT_SECRET) |
| `DEMO_MODE` | `false` | Mock-data fallback on Google API failure; must be false in production |
| `ENABLE_SCHEDULER` | `true` | Advisory lock also prevents duplicate runs across replicas |
| `GROQ_API_KEY` | ✅ Configured | Real key set |
| `FRONTEND_URL` | ✅ Configured | http://localhost:3000 |
| `RAZORPAY_KEY_ID` | ❌ Empty | Set for billing |
| `RAZORPAY_KEY_SECRET` | ❌ Empty | Set for billing |

**Google APIs (enabled in project):**
1. My Business Account Management API ✅
2. Business Information API ✅
3. Google My Business API v4 ✅

---

## 🧪 Test Status (2026-07-03)

**62/62 tests passing** across 14 modules (`py -3 -m pytest tests/` from `backend/`; SQLite in-memory, no Docker required).

Notable coverage added in July 2026:
- `test_tenant_isolation.py` — cross-tenant 403s on reviews, replies, smart rules, brand voice, location creation
- OAuth state forgery rejection (raw client_id as state → 400)
- Review upsert / unknown-rating skip / Google-reply mirror (`test_reliability.py::TestReviewUpsert`)

> Historical note: before the July 2026 pass, 5 reliability tests and 1 alerts test were failing despite this file claiming all-pass. Test claims in docs must come from an actual run.

---

## 🔐 Security Hardening (July 2026)

| Fix | Detail |
|-----|--------|
| Tenant isolation audit | 13 cross-tenant holes fixed (reviews, replies, brand voice, smart rules, competitors, alerts, SEO, tickets, scheduled reports, chat agent, location creation); shared `check_review_access` helper added |
| OAuth CSRF | Signed 10-min JWT `state` tokens; forged callbacks rejected |
| Tokens at rest | `EncryptedToken` Fernet column type on `GoogleIntegration.access_token/refresh_token` and `Agency.google_oauth_client_secret`; legacy plaintext read-compatible |
| Startup guards | Production refuses to boot with default `JWT_SECRET`, missing `ENCRYPTION_KEY`, or `DEMO_MODE=true` |
| Mock data gating | Silent mock fallbacks removed; `DEMO_MODE` flag required; unknown ratings skipped |
| Scheduler | PostgreSQL advisory lock prevents duplicate jobs across workers/replicas |
| Schema authority | `create_all` skipped in production; Alembic is the sole migration path (migration `003` widens OAuth secret column) |
| Auth robustness | `decode_access_token(None)` returns 401 instead of crashing to 500 |

---

## 🚀 Current State

| Component | Status |
|-----------|--------|
| Google OAuth (real tokens) | ✅ Working for Tasty Burger Co. (single internal test tenant) |
| Google APIs (Account Mgmt v1, Business Info v1, My Business v4) | ✅ Enabled, responding; v4 remains correct for reviews (no deprecation announced) |
| Token refresh | ✅ 5-min pre-expiry buffer, naive/aware UTC normalized |
| Review sync | ✅ Incremental, upserts edits, mirrors Google-side replies, skips unknown ratings |
| Error behavior on API failure | ✅ Raises + surfaces via `google_api_error`; mock data only with `DEMO_MODE=true` |
| Scheduler (hourly sync) | ✅ Running, advisory-locked |
| GROQ AI (reply generation) | ✅ Real key configured (`openai/gpt-oss-120b`) |
| Frontend (integrations UI) | ✅ Full GBP setup page; StrictMode-safe callback |
| Docker Compose | ✅ Configured (start with `docker compose up`) |
| Paying customers | ⬜ 0 — see roadmap Phase 6 |
