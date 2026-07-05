# ReputationOS AI — Product Document

> AI-Powered Brand Reputation Intelligence Platform  
> Version 1.1.0 — 2026-07-03. Feature reference only; for readiness status see `product-roadmap.md` v2.0
> (built & security-hardened, pre-revenue; Phase 5 features frozen pending customer validation)

---

## 1. Product Overview

ReputationOS AI is a multi-tenant SaaS platform that helps marketing agencies and multi-location businesses monitor, manage, and improve their online reputation. It ingests reviews from Google Business Profile, applies AI to draft replies, surfaces sentiment and topic insights, tracks competitors, detects reputation crises, and generates executive reports.

### Core Value Propositions

| Outcome | How ReputationOS Delivers |
|---|---|
| Reduce manual review handling | AI-reply drafting with brand voice, smart rules for auto-reply, bulk operations |
| Improve response speed and quality | 2-option AI drafts, approval workflow, brand voice profiles, reply templates |
| Surface operational problems | Sentiment analysis, topic extraction, crisis detection, competitor benchmarking |
| Executive brand health visibility | Dashboard with reputation score, scheduled PDF/Excel/PPTX reports, custom dashboards |

### Target Market

- **Primary:** Marketing agencies managing multiple client accounts
- **Secondary:** Multi-location businesses, restaurant chains, healthcare groups, hotels, retail brands

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                 │
│  React 19 · TypeScript · Tailwind CSS · Zustand ·       │
│  TanStack Query · shadcn/ui components                  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────┐
│                   Backend API (FastAPI)                  │
│  Python 3.11 · SQLAlchemy 2.0 (async) · Pydantic 2 ·    │
│  APScheduler · Groq AI (LLM) · Razorpay (billing)       │
└────────────────────────┬────────────────────────────────┘
                         │ SQL
┌────────────────────────▼────────────────────────────────┐
│              PostgreSQL 16 (via asyncpg)                  │
│  Multi-tenant schema · Alembic migrations                │
└─────────────────────────────────────────────────────────┘
```

### Infrastructure (Docker Compose)

| Service | Image | Port |
|---|---|---|
| `postgres` | postgres:16-alpine | 5432 |
| `backend` | Custom (FastAPI + uvicorn) | 8000 |
| `frontend` | Custom (Next.js dev server) | 3000 |

---

## 3. Features by Domain

### 3.1 Review Management

| Feature | Details |
|---|---|
| Google Review Ingestion | OAuth 2.0 (CSRF-protected signed state) via Google Business Profile APIs (Account Mgmt v1, Business Info v1, My Business v4 for reviews); automatic hourly sync, incremental by updateTime; upserts review edits; mirrors owner replies posted on Google; skips unknown ratings; exponential backoff on failure (`min(2^failures, 24h)`); per-location 120s timeout |
| Manual Review Import | Create reviews manually via API/UI |
| Review Inbox | List, filter (rating, sentiment, source, reply status, date), search, detail view |
| Saved Views | Zustand + localStorage persisted filter presets; create, load, delete |

### 3.2 AI Reply System

| Feature | Details |
|---|---|
| AI Reply Drafting | Groq LLM (`openai/gpt-oss-120b`, temp 0.2); generates 2 options per review |
| Brand Voice Profiles | Tone, vocabulary notes, greeting/closing styles, personality traits, example replies |
| Smart Rules | Rating-range-based rules: auto-reply, approval required, escalate, never auto |
| Approval Workflow | Approve / reject / replace drafts; audit-logged |
| Reply Quality Controls | 2-option drafts, human-in-the-loop approval, brand voice enforcement |

### 3.3 Analytics & Insights

| Feature | Details |
|---|---|
| Reputation Score | Weighted calculation: 35% rating, 25% sentiment, 25% response rate, 15% volume |
| Dashboard KPIs | Avg rating, total reviews, response rate, sentiment index, review growth, 30-day trend |
| Sentiment Analysis | Positive/negative/neutral/mixed per review; emotion breakdown; distribution by source/location |
| Topic Extraction | Operational topics with sub-topics and sentiment scores |
| AI Recommendations | Up to 4 contextual recommendations (unreplied, negative, improvement, healthy) |

### 3.4 Competitor Intelligence

| Feature | Details |
|---|---|
| Competitor CRUD | Add/remove competitors per location |
| Comparative Analytics | Side-by-side rating, review count, sentiment distribution |
| AI SWOT Analysis | Groq-powered strengths, weaknesses, opportunities, executive summary |
| Sample Review Data | 12 seeded review templates for benchmarking — **labeled as sample data** end-to-end (`is_sample_data` API flag, UI banner, `[Sample data]` prefix in stored SWOT summaries) until a real competitor data source is wired; heuristic SWOT fallback disabled in production |

### 3.5 Forecasting

| Feature | Details |
|---|---|
| Predicted Rating | AI-powered next-month rating forecast |
| Predicted Volume | Expected review volume projection |
| Churn Risk Score | 0-100 risk indicator with color-coded severity |
| Historical Data | 6-month monthly aggregates (avg rating, volume) |
| Cache | 24-hour cache to minimize AI calls |

### 3.6 Crisis Detection

| Feature | Details |
|---|---|
| Detection Method | Groq AI classification + keyword heuristic fallback |
| Severity Levels | Critical, High, Medium |
| Categories | PR Crisis, Health/Safety, Legal, Spam, Fake Review |
| Dispatch | Automated Slack/Teams/Email webhook notification |
| Status Workflow | Open → Resolved / Ignored |

### 3.7 Reporting

| Feature | Details |
|---|---|
| On-Demand Reports | PDF (reportlab), Excel (openpyxl), PowerPoint (python-pptx) |
| Report Types | Weekly, monthly, quarterly; with KPI cards, sentiment distribution, topics, recommendations |
| Scheduled Reports | CRUD management; APScheduler checks every 5min; generates due reports; advances by 7/30/90 days |
| Custom Dashboards | Saved layouts with widget configuration; grid-based positioning; 10 widget types; CRUD API |

### 3.8 AI Copilot

| Feature | Details |
|---|---|
| Chat Agent | Groq-powered with tool use (reputation score, recent reviews, log complaint) |
| Manager Session | Authenticated, persistent chat sessions with message history |
| Customer Widget | Public unauthenticated widget; configurable brand name/color |
| Streaming | NDJSON streaming responses |

### 3.9 Customer Journey Intelligence

| Feature | Details |
|---|---|
| Customer Profiles | Track customers across touchpoints |
| Touchpoints | Record interactions (review, chat, ticket, etc.) |
| Support Tickets | Create, update status, resolve; source tracking (chat, email, etc.) |
| Funnel Analytics | 90-day engagement funnel (total → reviewed → chatted → ticketed) |

### 3.10 Public API & Webhooks

| Feature | Details |
|---|---|
| API Key Management | SHA-256 hashed keys with `rpk_` prefix; CRUD API + management UI; scoped permissions |
| API Authentication | `X-API-Key` header auth in `dependencies.py` alongside Bearer JWT |
| Generic Webhooks | HMAC-SHA256 signed payloads; 6 event types; 3-retry backoff (60s/300s/900s); delivery history |
| Event Types | `review.created`, `reply.posted`, `crisis.detected`, `sync.completed`, `report.generated`, `score.changed` |

### 3.11 Billing & Plans

| Tier | Price | Features |
|---|---|---|
| Trial | Free (14 days) | 1 location, basic AI replies, standard reporting |
| Starter | $19/mo | Up to 3 locations, standard AI, basic reporting, email support |
| Pro | $49/mo | Unlimited locations, advanced AI Copilot, competitor & forecasting, custom branding, priority support, API access, webhooks |
| Enterprise | Custom | Everything in Pro, SSO/SAML, dedicated support, custom SLA |

### 3.12 Review Generation (Campaigns)

| Feature | Details |
|---|---|
| Campaigns | SMS / email / WhatsApp review-request campaigns per location (Twilio + SendGrid; providers must be configured and consent/opt-out compliance handled before selling) |
| Public Review Funnel | `/review-funnel` landing page — **compliant, non-gating** (2026-07-05): every rating gets the identical next step (public Google review option plus optional private feedback); rating-based routing is prohibited by Google review policy and the FTC review rule and must not be reintroduced |
| QR Codes | Per-campaign QR code generation |
| Employee Leaderboard | Conversion tracking per employee with 30-day leaderboard |

### 3.13 White-Label & Multi-Tenant

| Feature | Details |
|---|---|
| Multi-Tenant | Agency → Client → Location hierarchy |
| Branding Config | Company name, logo, favicon, primary/secondary/accent colors, font, dark mode default, sidebar style, custom CSS |
| Role-Based Access | 7 roles with numeric levels; scope enforcement per location/client/agency |

---

## 4. Security & Compliance

### Authentication

| Measure | Implementation |
|---|---|
| Password Policy | Min 8 chars, uppercase + lowercase + digit + special char; strength meter; bcrypt hashing |
| Rate Limiting | 5 attempts per 300s per IP on login (HTTP 429) |
| Session Management | Stateless JWT (HS256); `exp`/`iat`/`jti` claims; 24h expiry |
| MFA | TOTP (RFC 6238) via pyotp; Google Authenticator/Authy; admin-only; QR code setup |
| Account Recovery | 48-byte cryptographically random tokens; bcrypt-hashed; 1-hour expiry; single-use |

### Authorization

| Mechanism | Details |
|---|---|
| RBAC | 7 roles (super_admin 100 → read_only 10) |
| Scope Checks | `check_location_access()`, `verify_client_access()`, `check_review_access()` per endpoint; full tenant-isolation audit completed July 2026 with regression tests |
| Subscription Gate | `SubscriptionRequired` dependency on all 18 data routers |
| OAuth CSRF | Signed 10-min JWT state tokens on the Google connect flow |

### Data Protection

| Area | Implementation |
|---|---|
| Encryption in Transit | HSTS, restricted CORS, HTTPS recommended |
| Security Headers | HSTS, X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy |
| Encryption at Rest | Google OAuth tokens + agency client secrets Fernet-encrypted (column-level, `ENCRYPTION_KEY`); bcrypt for passwords; general PII unencrypted |
| Startup Guards | Production boot refused with default JWT_SECRET, missing ENCRYPTION_KEY, or DEMO_MODE enabled |
| Audit Logging | Login, password change, approve/reject reply, smart rules changes; 90-day retention; daily purge |
| GDPR Export | JSON export of all user data (`/api/users/me/export`) |
| Account Deletion | Anonymization (`/api/users/me/delete`) |

---

## 5. Technology Stack

### Backend

| Category | Technologies |
|---|---|
| Framework | FastAPI 0.115 (Python 3.11), uvicorn 0.34 |
| ORM | SQLAlchemy 2.0 (async) with asyncpg |
| Auth | python-jose (JWT), passlib (bcrypt), pyotp (TOTP) |
| AI | Groq SDK (`openai/gpt-oss-120b`, temp 0.2, 3 retries) |
| Reports | reportlab (PDF), openpyxl (Excel), python-pptx (PowerPoint) |
| Scheduling | APScheduler 3.11 |
| Billing | Razorpay 1.4 |
| Validation | Pydantic 2, pydantic-settings |

### Frontend

| Category | Technologies |
|---|---|
| Framework | Next.js 15 (App Router), React 19 |
| Styling | Tailwind CSS, shadcn/ui components |
| State | Zustand (persist middleware), TanStack Query |
| HTTP | Axios with interceptors |
| Fonts | Inter, Outfit (via next/font) |

### Infrastructure

| Component | Technology |
|---|---|
| Database | PostgreSQL 16 (alpine) |
| Containerization | Docker Compose |
| Migrations | Alembic |

---

## 6. API Surface

### Public Endpoints (no auth)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Account registration |
| POST | `/api/auth/login` | Login (returns JWT) |
| POST | `/api/auth/forgot-password` | Request password reset |
| POST | `/api/auth/reset-password` | Execute password reset |
| POST | `/api/billing/webhook` | Razorpay payment webhook |
| POST | `/api/chat/widget/{client_id}` | Customer widget chat |

### Authenticated Endpoints (JWT or API Key)

| Domain | Endpoints |
|---|---|
| Auth | `GET /api/auth/me`, `PATCH /api/auth/password`, `POST /api/auth/mfa/*`, `GET /api/auth/mfa/status` |
| Tenants | `GET/POST /api/agencies`, `GET/POST /api/clients`, `GET/POST /api/locations` |
| Reviews | `GET/POST /api/reviews`, `GET /api/reviews/{id}`, `POST /api/reviews/{id}/generate-reply`, `POST /api/reviews/{id}/reply` |
| Replies | `PATCH /api/replies/{id}/approve`, `PATCH /api/replies/{id}/reject` |
| Analytics | `GET /api/dashboard`, `GET /api/analytics/sentiment` |
| Brand Voice | `GET/PUT /api/brand-voice/{client_id}` |
| Smart Rules | `GET/PUT /api/smart-rules/{location_id}` |
| Branding | `GET/PUT /api/branding/{agency_id}` |
| Reports | `POST /api/reports/generate`, `GET/POST/PATCH/DELETE /api/reports/scheduled` |
| Users | `GET/POST /api/users`, `GET /api/users/me/export`, `DELETE /api/users/me` |
| Google Auth | `GET /api/integrations/google/*` |
| Chat | `POST /api/chat/manager` |
| Competitors | `GET/POST/DELETE /api/competitors`, `GET /api/competitors/analytics`, `GET/POST /api/competitors/analysis` |
| Alerts | `GET/PATCH /api/alerts`, `GET/POST /api/alerts/integrations` |
| Forecasting | `GET /api/forecasting` |
| Billing | `GET /api/billing/status`, `GET /api/billing/plans`, `POST /api/billing/checkout`, `PATCH /api/billing/update` |
| Audit | `GET /api/audit` |
| API Keys | `GET/POST/PATCH/DELETE /api/api-keys` |
| Webhooks | `GET/POST/PATCH/DELETE /api/webhooks/endpoints`, `GET /api/webhooks/deliveries`, `GET /api/webhooks/event-types` |
| Dashboards | `GET/POST /api/dashboards`, `GET/PATCH/DELETE /api/dashboards/{id}` |
| Customer Journey | `POST /api/customer-journey/touchpoints`, `GET /api/customer-journey/funnel`, `GET/PATCH /api/customer-journey/tickets` |
| Health | `GET /api/health` |

---

## 7. AI Architecture

### Models Used

| Task | Model | Provider | Temperature |
|---|---|---|---|
| Review reply drafting | `openai/gpt-oss-120b` | Groq | 0.2 |
| Sentiment analysis | `openai/gpt-oss-120b` | Groq | 0.2 |
| Topic extraction | `openai/gpt-oss-120b` | Groq | 0.2 |
| Crisis detection | `openai/gpt-oss-120b` | Groq | 0.2 |
| Competitor SWOT | `openai/gpt-oss-120b` | Groq | 0.2 |
| Forecasting | `openai/gpt-oss-120b` | Groq | 0.2 |
| Chat Copilot | `openai/gpt-oss-120b` | Groq | 0.2 |

### Fallback Behavior

When Groq API key is missing or set to placeholder `"your-..."`:
- AI features return mock/fallback responses
- Sentiment: keyword-based heuristic classification
- Crisis: keyword pattern matching
- Forecasting: reasonable default values
- Competitor analysis: keyword-based SWOT generation

**Google data is different:** Google API failures raise errors and surface in the UI
(`google_api_error`). Mock review/location data is only generated when `DEMO_MODE=true`
(never allowed in production — startup guard) or in the explicit `test-client-id` test mode.
Review data is never silently fabricated for real tenants.

### Rate Limits & Caching

| Feature | Cache | Purpose |
|---|---|---|
| Forecasting | 24-hour cache | Avoid repeated AI calls for same location |
| Sentiment Analysis | Per-review (computed on import) | One-time computation |
| Competitor Analysis | Daily (update if exists) | Refresh once per day |
| Chat Sessions | Per-session (DB persisted) | Conversation continuity |

---

## 8. Scheduled Jobs (APScheduler)

A PostgreSQL advisory lock ensures only one process runs jobs when multiple workers/replicas
are deployed; `ENABLE_SCHEDULER=false` opts a replica out explicitly.

| Job | Interval | Description |
|---|---|---|
| `sync_google_reviews` | Every 1 hour | Incremental fetch of new/edited reviews for all mapped locations; upserts edits; concurrency guard; 120s per-location timeout |
| `process_scheduled_reports` | Every 5 minutes | Check for due scheduled reports; generate PDF/Excel/PPTX; advance next_run_at |
| `cleanup_old_audit_logs` | Daily | Delete audit logs older than 90 days (configurable) |
| `retry_webhook_deliveries` | Every 5 minutes | Retry failed webhook deliveries up to 3 attempts |

---

## 9. UI Routes

| Route | Page |
|---|---|
| `/login` | Login with MFA challenge support |
| `/register` | Registration with password strength meter |
| `/forgot-password` | Password reset request |
| `/reset-password` | Password reset with token |
| `/dashboard` | Main dashboard with reputation score and KPIs |
| `/dashboard/reviews` | Review inbox with filters and saved views |
| `/dashboard/analytics` | Sentiment deep-dive and analytics |
| `/dashboard/analytics/forecasting` | AI forecasting page |
| `/dashboard/reports` | On-demand and scheduled report management |
| `/dashboard/custom-dashboards` | Custom dashboard builder |
| `/dashboard/competitors` | Competitor management and SWOT analysis |
| `/dashboard/alerts` | Crisis alerts and webhook integrations |
| `/dashboard/copilot` | AI chat assistant |
| `/dashboard/integrations` | Google integrations status |
| `/dashboard/customer-journey` | Funnel analytics and touchpoints |
| `/dashboard/settings` | Settings hub |
| `/dashboard/settings/branding` | White-label branding |
| `/dashboard/settings/brand-voice` | AI reply tone configuration |
| `/dashboard/settings/smart-rules` | Auto-reply rules |
| `/dashboard/settings/team` | User management |
| `/dashboard/settings/security` | Password, MFA, data export/delete |
| `/dashboard/settings/api-keys` | API key management |
| `/dashboard/settings/webhooks` | Webhook endpoint management |
| `/dashboard/settings/audit-logs` | Audit trail viewer |
| `/dashboard/settings/billing` | Plan management and checkout |
| `/dashboard/settings/integrations` | Global API credentials |

---

## 10. Development & Operations

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Quick Start
```bash
docker compose up -d
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API docs (Swagger): http://localhost:8000/docs
```

### Demo Credentials
- Email: `admin@reputationos.ai`
- Password: `demo1234`

### Environment Variables (`.env`)
```env
DATABASE_URL=postgresql+asyncpg://repuser:reppass@postgres:5432/reputationos
ENVIRONMENT=development            # "production" enforces startup security guards
JWT_SECRET=<generate-strong-random-secret>
JWT_EXPIRY_HOURS=24
ENCRYPTION_KEY=<fernet-key>        # required in production; python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
DEMO_MODE=false                    # mock Google data fallback; never true in production
ENABLE_SCHEDULER=true              # advisory lock also dedupes across replicas
GROQ_API_KEY=<your-groq-api-key>
FRONTEND_URL=http://localhost:3000
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
AUDIT_LOG_RETENTION_DAYS=90
RATE_LIMIT_PER_WINDOW=5
RATE_LIMIT_WINDOW_SECONDS=300
RAZORPAY_KEY_ID=<your-razorpay-key>
RAZORPAY_KEY_SECRET=<your-razorpay-secret>
```

### Key Commands
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend

# Run database migrations
docker compose exec backend alembic upgrade head

# Access database
docker compose exec postgres psql -U repuser -d reputationos

# Rebuild after dependency changes
docker compose build backend
docker compose up -d
```

---

## 11. Known Gaps & Deferred Items

| Item | Status / Reason |
|---|---|
| Backup and restore process | **Open — blocker before first paying customer** (roadmap Phase 6) |
| External penetration test / security review | Open — SOC 2 posture is self-assessed until done |
| Formal incident response plan | Organizational, not product |
| Vendor security assessment | Procurement process |
| Data classification policy | Governance documentation |
| Column-level encryption | Done for OAuth tokens/secrets (July 2026); general PII fields remain unencrypted |
| Token revocation (blacklist) | Stateless JWT design choice; JWTs in localStorage (httpOnly cookies would be safer) |
| GBP API quota approval | Each agency's Google Cloud project starts at quota 0 until Google approves access — onboarding dependency |
| Industry-specific workflows | Deferred beyond v1 scope |
| Multi-AI-provider support | Keep simple for v1 |
| Complex enterprise procurement | Future phase |

---

## 12. KPIs & Success Metrics

> Current measured values live in the KPI scoreboard in `product-roadmap.md` §6 (updated monthly).
> As of 2026-07-03 all metrics below are at zero or not yet instrumented.

### Acquisition
- Trial-to-active conversion rate
- Demo-to-trial conversion rate
- Time to first value (minutes from signup to first review)

### Activation
- First data source connected
- First review imported
- First AI reply generated
- First report exported

### Retention
- Weekly active accounts
- Weekly active users
- Review response rate
- Report usage frequency
- Alert resolution rate

### Revenue
- Plan upgrade rate (trial → paid, starter → pro)
- Expansion revenue per account
- Churn rate
- Average revenue per account (ARPA)
