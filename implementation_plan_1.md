# ReputationOS AI — Implementation Plan (POC)

> **Historical document (banner added 2026-07-03):** original pre-build POC plan, kept for reference.
> The shipped product diverged in places (AI model is `openai/gpt-oss-120b`, not Llama 3.3 70B).
> Current architecture: `docs/knowledge-graph.md`. Current status: `docs/product-roadmap.md` v2.0.
> Note: `implementation_plan_1.md` is an identical duplicate of `implementation_plan.md`.

AI-Powered Brand Reputation Intelligence Platform — lightweight POC build with a simplified tech stack, demo data seeding, and white-label branding support.

---

## User Review Required

> [!IMPORTANT]
> **Groq Model**: Plan uses **Llama 3.3 70B** via Groq API for all AI tasks (sentiment, replies, topic extraction). Groq's free tier allows 30 RPM / 15,000 TPD. Confirm if you have a Groq API key or need guidance to get one.

> [!IMPORTANT]
> **Google Business Profile**: Users will manually paste their GBP data (Place ID, reviews export) through the UI. No Google OAuth or API integration for POC. Reviews can also be added manually or via the seed data. Confirm this is acceptable.

> [!NOTE]
> **Deferred to Future Scope**: Billing/subscriptions, SMS/email notifications, Keycloak/Auth0, Elasticsearch, Qdrant vector DB, RabbitMQ/Kafka, Kubernetes, multi-cloud deployment, competitor intelligence, crisis detection, AI forecasting.

---

## Tech Stack (POC — Lightweight)

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | Next.js 15 + TypeScript | App Router, SSR, API routes |
| **UI Components** | shadcn/ui + Tailwind CSS | Pre-built accessible components, fast iteration |
| **Charts** | Recharts | Lightweight, React-native charting |
| **State** | Zustand + TanStack Query | Minimal boilerplate, smart server-state caching |
| **Backend** | FastAPI + Python | Fast API development, async support |
| **Database** | PostgreSQL 16 | Single DB, no need for Redis/ES for POC |
| **Migrations** | Alembic | Schema versioning |
| **AI** | Groq (Llama 3.3 70B) | Ultra-fast inference, free tier available |
| **Background Tasks** | FastAPI BackgroundTasks + APScheduler | No message queue needed for POC |
| **Auth** | Simple JWT (username/password) | bcrypt password hashing, JWT tokens |
| **Infrastructure** | Docker Compose | Single command to spin up everything |

---

## Architecture Overview

```mermaid
graph TB
    subgraph Frontend["Frontend — Next.js + shadcn/ui"]
        Pages["Pages (App Router)"]
        Components["shadcn/ui Components"]
        Store["Zustand + TanStack Query"]
    end

    subgraph Backend["Backend — FastAPI"]
        API["REST API"]
        AuthMW["JWT Auth Middleware"]
        Services["Service Layer"]
        AI["AI Engine (Groq)"]
        BG["Background Tasks"]
    end

    subgraph Data["PostgreSQL"]
        Tenants["Tenants & Branding"]
        Reviews["Reviews & Replies"]
        Sentiment["Sentiment & Topics"]
        Scores["Reputation Scores"]
    end

    Pages --> Store --> API
    API --> AuthMW --> Services
    Services --> AI
    Services --> Data
    BG --> Data
    BG --> AI
```

---

## Proposed Changes

All files are **[NEW]** (greenfield project).

---

### Component 1: Project Foundation & Docker

#### [NEW] Root Structure

```
brand-reputation/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│
└── frontend/
    ├── Dockerfile
    └── src/
```

#### [NEW] [docker-compose.yml](file:///c:/Users/USER/brand-reputation/docker-compose.yml)

Three services only:
- **postgres**: PostgreSQL 16, port 5432, volume-persisted
- **backend**: FastAPI (uvicorn), port 8000, hot-reload via volume mount
- **frontend**: Next.js dev server, port 3000, hot-reload via volume mount

#### [NEW] [.env.example](file:///c:/Users/USER/brand-reputation/.env.example)

```env
# Database
DATABASE_URL=postgresql://repuser:reppass@postgres:5432/reputationos

# Auth
JWT_SECRET=change-me-in-production
JWT_EXPIRY_HOURS=24

# AI
GROQ_API_KEY=your-groq-api-key

# App
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

---

### Component 2: Backend — FastAPI

#### [NEW] Backend Structure

```
backend/
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── alembic/
│   └── versions/
│
├── app/
│   ├── main.py                     # FastAPI app, CORS, startup events
│   ├── config.py                   # Pydantic BaseSettings
│   ├── database.py                 # SQLAlchemy engine & session
│   │
│   ├── core/
│   │   ├── auth.py                 # JWT create/verify, password hashing
│   │   ├── dependencies.py         # get_current_user, get_db, get_tenant
│   │   └── permissions.py          # Role-based access decorators
│   │
│   ├── models/
│   │   ├── base.py                 # Base model (id, created_at, updated_at)
│   │   ├── tenant.py              # Agency, Client, Location, BrandingConfig
│   │   ├── user.py                # User (email, hashed_password, role)
│   │   ├── review.py             # Review, ReviewReply
│   │   ├── sentiment.py          # SentimentResult, TopicResult
│   │   ├── analytics.py          # ReputationScore
│   │   └── brand_voice.py        # BrandVoiceProfile
│   │
│   ├── schemas/                   # Pydantic request/response models
│   │   ├── auth.py               # LoginRequest, TokenResponse, RegisterRequest
│   │   ├── tenant.py             # Agency/Client/Location CRUD schemas
│   │   ├── review.py             # Review list/detail/create schemas
│   │   ├── analytics.py          # Dashboard data, score schemas
│   │   ├── brand_voice.py        # Brand voice config schemas
│   │   └── branding.py           # White-label branding schemas
│   │
│   ├── api/
│   │   ├── auth.py               # POST /login, /register, /me
│   │   ├── tenants.py            # CRUD agencies, clients, locations
│   │   ├── reviews.py            # List, filter, search reviews
│   │   ├── replies.py            # Generate AI reply, approve, post
│   │   ├── analytics.py          # Dashboard data, reputation score
│   │   ├── brand_voice.py        # Brand voice CRUD
│   │   ├── branding.py           # White-label branding CRUD
│   │   ├── reports.py            # Generate & download reports
│   │   └── users.py              # User management (admin)
│   │
│   ├── services/
│   │   ├── auth_service.py       # Login, register, token logic
│   │   ├── review_service.py     # Review CRUD + filtering
│   │   ├── reply_service.py      # AI reply orchestration
│   │   ├── sentiment_service.py  # Sentiment analysis orchestration
│   │   ├── analytics_service.py  # Reputation score calculation
│   │   ├── report_service.py     # PDF/Excel report generation
│   │   └── branding_service.py   # White-label config management
│   │
│   ├── ai/
│   │   ├── groq_client.py        # Groq API client wrapper
│   │   ├── sentiment.py          # Sentiment classification prompt + parser
│   │   ├── topic_extraction.py   # Topic extraction prompt + parser
│   │   ├── review_reply.py       # Reply generation with brand voice
│   │   └── prompts.py            # All prompt templates (centralized)
│   │
│   └── seed/
│       ├── seed_data.py          # Main seeder script
│       ├── demo_reviews.json     # 200+ realistic demo reviews
│       ├── demo_agencies.json    # Sample agencies with branding
│       └── demo_users.json       # Demo users for each role
│
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_reviews.py
    ├── test_ai.py
    └── test_analytics.py
```

#### Key Backend Decisions

**Authentication** — Simple JWT, no OAuth:
```
POST /api/auth/register  → { email, password, name }  → 201 + JWT
POST /api/auth/login      → { email, password }         → 200 + JWT
GET  /api/auth/me         → (Bearer token)              → User profile
```
Passwords hashed with bcrypt. JWT tokens with configurable expiry. Roles assigned by admin.

**Multi-Tenancy** — Column-level tenant isolation:
```
Platform → Agency → Client → Location
```
Every model includes `agency_id` or `client_id`. Middleware resolves tenant from JWT user context. All queries auto-filtered.

**RBAC** — 7 roles enforced via decorators:
```python
@require_role(["agency_admin", "client_admin"])
async def create_location(...):
```

**White-Label Branding** — Per-agency config stored in `branding_configs` table:

| Field | Description |
|-------|------------|
| `agency_id` | Owner agency |
| `logo_url` | Custom logo |
| `favicon_url` | Custom favicon |
| `primary_color` | Brand primary color (hex) |
| `secondary_color` | Brand secondary color (hex) |
| `accent_color` | Accent color (hex) |
| `company_name` | Display name (replaces "ReputationOS") |
| `custom_domain` | Custom domain (future) |
| `font_family` | Custom font preference |
| `dark_mode_default` | Default to dark mode |
| `sidebar_style` | Sidebar appearance |
| `login_bg_image` | Custom login background |
| `email_header_html` | Custom email header (future) |

**Google Business Profile** — Manual input flow:
1. User enters Google Place ID in the integrations page
2. (Optional) User uploads a CSV/JSON export of reviews
3. Reviews are stored in the `reviews` table with `source = "google"`
4. Manual "Add Review" form also available for quick entry

---

### Component 3: Database Schema

#### [NEW] Core Tables (Alembic initial migration)

```sql
-- TENANT HIERARCHY
CREATE TABLE agencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE branding_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE,
    company_name VARCHAR(255),
    logo_url TEXT,
    favicon_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#6366f1',
    secondary_color VARCHAR(7) DEFAULT '#8b5cf6',
    accent_color VARCHAR(7) DEFAULT '#06b6d4',
    font_family VARCHAR(100) DEFAULT 'Inter',
    dark_mode_default BOOLEAN DEFAULT true,
    sidebar_style VARCHAR(20) DEFAULT 'modern',
    login_bg_image TEXT,
    custom_css TEXT,
    UNIQUE(agency_id)
);

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    google_place_id VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- USERS & AUTH
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'read_only',
    agency_id UUID REFERENCES agencies(id),
    client_id UUID REFERENCES clients(id),
    location_id UUID REFERENCES locations(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- REVIEWS
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL DEFAULT 'google',
    source_review_id VARCHAR(255),
    author_name VARCHAR(255),
    author_image_url TEXT,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    text TEXT,
    review_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source, source_review_id)
);

CREATE TABLE review_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID REFERENCES reviews(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',  -- draft, approved, posted, rejected
    generated_by VARCHAR(20) DEFAULT 'ai',  -- ai, manual
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SENTIMENT & TOPICS
CREATE TABLE sentiment_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID UNIQUE REFERENCES reviews(id) ON DELETE CASCADE,
    sentiment VARCHAR(20) NOT NULL,  -- positive, negative, neutral, mixed
    confidence FLOAT,
    emotions TEXT[],  -- array of detected emotions
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE topic_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID REFERENCES reviews(id) ON DELETE CASCADE,
    topic VARCHAR(100) NOT NULL,
    sub_topic VARCHAR(100),
    sentiment VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ANALYTICS
CREATE TABLE reputation_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
    score_date DATE NOT NULL,
    overall_score FLOAT,
    avg_rating FLOAT,
    review_volume INTEGER,
    sentiment_score FLOAT,
    response_rate FLOAT,
    components JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(location_id, score_date)
);

-- BRAND VOICE
CREATE TABLE brand_voice_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    tone VARCHAR(50) DEFAULT 'professional',
    vocabulary_notes TEXT,
    greeting_style TEXT,
    closing_style TEXT,
    example_replies TEXT[],
    personality_traits TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id)
);

-- SMART RULES
CREATE TABLE smart_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
    min_rating INTEGER NOT NULL,
    max_rating INTEGER NOT NULL,
    action VARCHAR(30) NOT NULL,  -- auto_reply, approval_required, escalate, never_auto
    notify_roles TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### Component 4: Frontend — Next.js + shadcn/ui

#### [NEW] Frontend Structure

```
frontend/
├── Dockerfile
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── components.json              # shadcn/ui config
│
├── public/
│   ├── logo.svg
│   └── favicon.ico
│
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout — loads branding, fonts
│   │   ├── globals.css          # Tailwind base + CSS custom properties for branding
│   │   ├── page.tsx             # Redirect to /login or /dashboard
│   │   │
│   │   ├── login/
│   │   │   └── page.tsx         # Login form (email + password)
│   │   ├── register/
│   │   │   └── page.tsx         # Registration form
│   │   │
│   │   └── (dashboard)/
│   │       ├── layout.tsx       # Sidebar + topbar shell (uses branding)
│   │       ├── page.tsx         # ★ Reputation Dashboard (Module 1)
│   │       │
│   │       ├── reviews/
│   │       │   ├── page.tsx     # Review list — filters, search, bulk actions
│   │       │   └── [id]/
│   │       │       └── page.tsx # Review detail — sentiment, topics, reply
│   │       │
│   │       ├── analytics/
│   │       │   ├── page.tsx     # Analytics overview — charts, trends
│   │       │   └── sentiment/
│   │       │       └── page.tsx # Sentiment deep-dive
│   │       │
│   │       ├── reports/
│   │       │   └── page.tsx     # Report generation & download
│   │       │
│   │       ├── integrations/
│   │       │   └── page.tsx     # Add GBP Place ID, upload reviews CSV
│   │       │
│   │       └── settings/
│   │           ├── page.tsx         # General settings
│   │           ├── brand-voice/
│   │           │   └── page.tsx     # Brand voice configuration
│   │           ├── smart-rules/
│   │           │   └── page.tsx     # Reply automation rules
│   │           ├── branding/
│   │           │   └── page.tsx     # ★ White-label branding config
│   │           └── team/
│   │               └── page.tsx     # User management
│   │
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components (auto-generated)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── table.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── avatar.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── sheet.tsx        # Mobile sidebar
│   │   │   └── separator.tsx
│   │   │
│   │   ├── layout/
│   │   │   ├── sidebar.tsx          # Collapsible sidebar with branding
│   │   │   ├── topbar.tsx           # Top navigation bar
│   │   │   ├── tenant-switcher.tsx  # Agency/Client/Location selector
│   │   │   └── mobile-nav.tsx       # Sheet-based mobile navigation
│   │   │
│   │   ├── dashboard/
│   │   │   ├── reputation-score-card.tsx  # Animated circular score
│   │   │   ├── rating-trend-chart.tsx     # Line chart (Recharts)
│   │   │   ├── sentiment-donut.tsx        # Donut chart
│   │   │   ├── review-volume-chart.tsx    # Bar chart
│   │   │   ├── ai-recommendations.tsx     # AI suggestion cards
│   │   │   ├── recent-reviews.tsx         # Latest review feed
│   │   │   └── stats-grid.tsx             # KPI stat cards
│   │   │
│   │   ├── reviews/
│   │   │   ├── review-card.tsx            # Review display card
│   │   │   ├── review-filters.tsx         # Rating, sentiment, source filters
│   │   │   ├── reply-composer.tsx         # Manual reply editor
│   │   │   ├── ai-reply-generator.tsx     # AI reply with brand voice
│   │   │   └── approval-queue.tsx         # Pending replies list
│   │   │
│   │   ├── analytics/
│   │   │   ├── sentiment-breakdown.tsx    # Sentiment bar/pie charts
│   │   │   ├── topic-analysis.tsx         # Topic treemap/bar chart
│   │   │   ├── emotion-radar.tsx          # Emotion radar chart
│   │   │   └── trend-line.tsx             # Generic trend line
│   │   │
│   │   └── branding/
│   │       ├── branding-form.tsx          # White-label config form
│   │       ├── color-picker.tsx           # Color picker component
│   │       ├── logo-uploader.tsx          # Logo upload with preview
│   │       └── branding-preview.tsx       # Live preview of branding
│   │
│   ├── hooks/
│   │   ├── use-auth.ts              # Auth state & login/logout
│   │   ├── use-tenant.ts            # Current tenant context
│   │   ├── use-branding.ts          # Load & apply white-label branding
│   │   └── use-reviews.ts           # Review queries
│   │
│   ├── lib/
│   │   ├── api.ts                   # Axios client with JWT interceptor
│   │   ├── utils.ts                 # cn() helper, formatters
│   │   └── constants.ts             # Route paths, role names
│   │
│   ├── stores/
│   │   ├── auth-store.ts            # JWT token, user profile
│   │   ├── tenant-store.ts          # Active agency/client/location
│   │   └── branding-store.ts        # Cached branding config
│   │
│   └── types/
│       ├── review.ts
│       ├── tenant.ts
│       ├── user.ts
│       ├── analytics.ts
│       └── branding.ts
```

#### White-Label Branding System

The branding system uses **CSS custom properties** so the entire UI theme can be swapped at runtime:

```css
/* globals.css — defaults */
:root {
  --brand-primary: 99 102 241;      /* indigo-500 */
  --brand-secondary: 139 92 246;    /* violet-500 */
  --brand-accent: 6 182 212;        /* cyan-500 */
  --brand-font: 'Inter', sans-serif;
  --brand-logo: url('/logo.svg');
  --brand-name: 'ReputationOS AI';
}
```

On login, the `use-branding` hook fetches the agency's branding config and injects CSS variables dynamically. The sidebar logo, app title, color palette, and font all update instantly — no page reload needed.

#### Key Dashboard Page Layout

```
┌─────────────────────────────────────────────────────┐
│  [Logo]  ReputationOS AI          🔔  👤 John Doe  │
├──────┬──────────────────────────────────────────────┤
│      │                                              │
│  📊  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│ Dash │  │ Rep.    │ │ Avg     │ │ Review  │       │
│      │  │ Score   │ │ Rating  │ │ Volume  │       │
│  💬  │  │  78/100 │ │  4.2 ★  │ │  1,247  │       │
│ Rev. │  └─────────┘ └─────────┘ └─────────┘       │
│      │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  📈  │  │ Resp.   │ │ Sentim. │ │ Growth  │       │
│ Ana. │  │ Rate    │ │ Score   │ │  +12%   │       │
│      │  │  89%    │ │  0.72   │ │  ↑ ↑    │       │
│  📄  │  └─────────┘ └─────────┘ └─────────┘       │
│ Rep. │                                              │
│      │  ┌──────────────────┐ ┌─────────────────┐   │
│  🔗  │  │                  │ │                 │   │
│ Int. │  │  Rating Trend    │ │  Sentiment      │   │
│      │  │  (Line Chart)    │ │  (Donut Chart)  │   │
│  ⚙️  │  │                  │ │                 │   │
│ Set. │  └──────────────────┘ └─────────────────┘   │
│      │                                              │
│      │  ┌──────────────────────────────────────┐   │
│      │  │  AI Recommendations                  │   │
│      │  │  • Reply to 12 pending reviews       │   │
│      │  │  • 3 negative reviews need attention  │   │
│      │  │  • Customer satisfaction trending ↑   │   │
│      │  └──────────────────────────────────────┘   │
│      │                                              │
│      │  ┌──────────────────────────────────────┐   │
│      │  │  Recent Reviews (live feed)          │   │
│      │  │  ★★★★★  "Great service..." - 2h ago  │   │
│      │  │  ★★☆☆☆  "Long wait..." - 5h ago      │   │
│      │  └──────────────────────────────────────┘   │
└──────┴──────────────────────────────────────────────┘
```

---

### Component 5: AI Engine — Groq (Llama 3.3 70B)

#### [NEW] [backend/app/ai/groq_client.py](file:///c:/Users/USER/brand-reputation/backend/app/ai/groq_client.py)

Wrapper around the Groq Python SDK:
- Model: `llama-3.3-70b-versatile`
- Structured JSON output parsing
- Retry logic with exponential backoff
- Rate limit awareness (30 RPM free tier)

#### [NEW] [backend/app/ai/prompts.py](file:///c:/Users/USER/brand-reputation/backend/app/ai/prompts.py)

Centralized prompt templates:

**Sentiment Analysis Prompt**:
```
Analyze the following customer review and return JSON:
{
  "sentiment": "positive|negative|neutral|mixed",
  "confidence": 0.0-1.0,
  "emotions": ["happy", "angry", "frustrated", ...]
}
Review: "{review_text}"
```

**Topic Extraction Prompt**:
```
Extract business topics from this review. Return JSON array:
[{ "topic": "...", "sub_topic": "...", "sentiment": "positive|negative|neutral" }]
Possible topics: Food, Staff, Service, Delivery, Billing, Pricing,
Hygiene, Ambiance, Parking, Wait Time, Product Quality, Location.
Review: "{review_text}"
```

**Review Reply Prompt**:
```
Generate a professional reply to this customer review.
Brand voice: {tone} | Greeting: {greeting_style} | Closing: {closing_style}
Business: {business_name} | Industry: {industry}
Rating: {rating}/5
Review: "{review_text}"

Return 2 reply options as JSON array. Each reply should be {tone},
personalized, and address specific points in the review.
```

#### AI Processing Pipeline

```mermaid
graph LR
    New["New Review Arrives"] --> S["Sentiment Analysis"]
    S --> T["Topic Extraction"]
    T --> Rules{"Smart Rules Check"}
    Rules -->|"★★★★★ or ★★★★☆"| Auto["Auto-Generate Reply"]
    Rules -->|"★★★☆☆"| Draft["Draft Reply → Queue"]
    Rules -->|"★★☆☆☆"| Escalate["Escalate + Draft"]
    Rules -->|"★☆☆☆☆"| Manual["Flag for Manual Reply"]
    Auto --> Voice["Apply Brand Voice"]
    Draft --> Voice
    Voice --> Store["Store Reply"]
```

All three AI calls (sentiment, topics, reply) use Groq for fast inference (~200ms per call with Groq vs ~2s with OpenAI).

---

### Component 6: Seed Data

#### [NEW] [backend/app/seed/seed_data.py](file:///c:/Users/USER/brand-reputation/backend/app/seed/seed_data.py)

Run via CLI: `python -m app.seed.seed_data`

Seeds the database with:

| Data | Count | Details |
|------|-------|---------|
| **Agencies** | 2 | "Stellar Digital Agency" (with custom branding), "RepBoost Agency" (default branding) |
| **Clients** | 4 | Restaurant chain, Hotel, Medical clinic, Retail store |
| **Locations** | 8 | 2 per client |
| **Users** | 10 | 1 super admin, 2 agency admins, 2 client admins, 2 marketing managers, 1 support, 1 branch manager, 1 read-only |
| **Reviews** | 200+ | Realistic reviews across all ratings (1–5★), varied industries |
| **Sentiment Results** | 200+ | Pre-analyzed sentiment for all seeded reviews |
| **Topic Results** | 400+ | Multiple topics per review |
| **Reputation Scores** | 90 days | Daily scores for all locations (historical trend data) |
| **Brand Voice Profiles** | 4 | One per client with industry-appropriate tone |
| **Smart Rules** | 8 | Default rule sets per location |
| **Review Replies** | 50 | Mix of AI-generated drafts and approved replies |
| **Branding Configs** | 2 | One custom-branded (purple theme + custom logo), one default |

**Demo Login Credentials**:
| Role | Email | Password |
|------|-------|----------|
| Super Admin | `admin@reputationos.ai` | `demo1234` |
| Agency Admin | `agency@stellar.digital` | `demo1234` |
| Client Admin | `manager@tastyburger.com` | `demo1234` |
| Marketing | `marketing@tastyburger.com` | `demo1234` |

---

## MVP Timeline (POC)

```mermaid
gantt
    title ReputationOS AI — POC Timeline
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d

    section Week 1 — Foundation
    Docker + project setup           :f1, 2026-07-07, 2d
    DB schema + Alembic migrations   :f2, after f1, 2d
    JWT auth (register/login)        :f3, after f2, 1d

    section Week 2 — Backend Core
    Tenant CRUD + RBAC               :b1, after f3, 2d
    Review CRUD + filtering          :b2, after b1, 2d
    Branding/white-label API         :b3, after b2, 1d

    section Week 3 — AI + Services
    Groq client + prompts            :a1, after b3, 1d
    Sentiment analysis pipeline      :a2, after a1, 1d
    Topic extraction pipeline        :a3, after a2, 1d
    Reply generation + brand voice   :a4, after a3, 1.5d
    Smart rules engine               :a5, after a4, 0.5d

    section Week 4 — Frontend
    Next.js + shadcn/ui setup        :fe1, after a5, 1d
    Auth pages + branding loader     :fe2, after fe1, 1d
    Dashboard page + charts          :fe3, after fe2, 2d
    Review management pages          :fe4, after fe3, 2d

    section Week 5 — Polish
    Analytics + sentiment pages      :fe5, after fe4, 1.5d
    Settings + branding config       :fe6, after fe5, 1.5d
    Seed data + demo setup           :s1, after fe6, 1d
    Testing + bug fixes              :t1, after s1, 1d
```

**Estimated POC Timeline**: ~4–5 weeks

---

## Verification Plan

### Automated Tests

```bash
# Backend — run all tests
docker compose exec backend pytest tests/ -v

# Backend — with coverage
docker compose exec backend pytest tests/ -v --cov=app

# Frontend — component tests
docker compose exec frontend npm test

# Lint
docker compose exec backend ruff check .
docker compose exec frontend npm run lint
```

### Manual Verification
- **Seed Data**: Run seeder, verify all demo data appears in the dashboard
- **Auth**: Login with each demo role, verify permissions
- **AI Pipeline**: Add a new review → verify sentiment + topics + reply auto-generated
- **White-Label**: Switch agency branding → verify logo, colors, and app name update live
- **Dashboard**: Verify all charts render with seed data, KPIs are accurate
- **Smart Rules**: Add reviews at each star level → verify correct action taken
- **Reports**: Generate and download PDF/Excel report
- **Responsive**: Test sidebar collapse, mobile nav on < 768px

### Smoke Test Checklist
- [ ] `docker compose up` starts all 3 services without errors
- [ ] Login page loads at `localhost:3000/login`
- [ ] Demo admin can login and see the dashboard
- [ ] Reputation score displays as animated circular gauge
- [ ] Charts show 90-day historical trend data
- [ ] Review list loads with filters working
- [ ] AI reply generates in < 2 seconds (Groq)
- [ ] White-label branding changes reflect immediately
- [ ] Different roles see appropriate navigation items
