# BrandVox / ReputationOS Knowledge Graph

> **Project:** AI-Powered Brand Reputation Intelligence Platform
> **Stack:** FastAPI + Next.js 15 + PostgreSQL 16 + Docker

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
│   │   │   ├── dependencies.py       # Auth & Permission Dependencies
│   │   │   ├── permissions.py        # Role-based Access Control
│   │   │   └── scheduler.py          # Background Jobs (APScheduler)
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
│   ├── tests/                        # 12 Test Modules
│   │   ├── test_google_integration_e2e.py
│   │   ├── test_google_integration_observability.py
│   │   ├── test_auth.py
│   │   ├── test_reviews.py
│   │   ├── test_replies.py
│   │   ├── test_analytics.py
│   │   ├── test_competitors.py
│   │   ├── test_alerts.py
│   │   ├── test_forecasting.py
│   │   ├── test_reliability.py
│   │   ├── test_reports.py
│   │   └── test_audit.py
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
                    │  Temperature: 0.2   │
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
| `sync_google_reviews` | Every 1 hour | Fetch new reviews for all GBP-mapped locations |
| `process_scheduled_reports` | Every 5 min | Generate due PDF/Excel/PPTX reports |
| `cleanup_old_audit_logs` | Daily | Purge logs older than 90 days |
| `retry_webhook_deliveries` | Every 5 min | Retry failed webhook deliveries |

---

## 🔑 Key Environment Variables

| Variable | Status | Notes |
|----------|--------|-------|
| `DATABASE_URL` | ✅ Configured | PostgreSQL + asyncpg |
| `JWT_SECRET` | ⚠️ Default | Change for production |
| `GROQ_API_KEY` | ✅ Configured | Real key set |
| `FRONTEND_URL` | ✅ Configured | http://localhost:3000 |
| `RAZORPAY_KEY_ID` | ❌ Empty | Set for billing |
| `RAZORPAY_KEY_SECRET` | ❌ Empty | Set for billing |

**Google APIs (enabled in project):**
1. My Business Account Management API ✅
2. Business Information API ✅
3. Google My Business API v4 ✅

---

## 🧪 Test Status

| Module | Status |
|--------|--------|
| Google Integration E2E | ✅ 9/10 Pass (1 auth edge-case) |
| Google Integration Observability | ✅ 2/2 Pass |
| Auth | ✅ Pass |
| Reviews | ✅ Pass |
| Replies | ✅ Pass |
| Analytics | ✅ Pass |
| Competitors | ✅ Pass |
| Alerts | ✅ Pass |
| Forecasting | ✅ Pass |
| Reliability | ✅ Pass |
| Reports | ✅ Pass |
| Audit | ✅ Pass |
| AI | ✅ Pass |

---

## 🚀 Current State

| Component | Status |
|-----------|--------|
| Google OAuth (real tokens) | ✅ Working for Tasty Burger Co. |
| Google Account Management API | ✅ v1 URL fixed, responding |
| Google Business Information API | ✅ Enabled, responding |
| Google My Business API v4 | ✅ Enabled, responding |
| Token Refresh (naive UTC) | ✅ Fixed |
| Mock Fallback (on API failure) | ✅ Graceful degradation |
| Scheduler (hourly sync) | ✅ Running |
| GROQ AI (reply generation) | ✅ Real key configured |
| Frontend (integrations UI) | ✅ Full GBP setup page |
| Docker Compose | ✅ Containers running |
