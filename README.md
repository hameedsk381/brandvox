# ReputationOS AI

AI-Powered Brand Reputation Intelligence Platform.

**Status:** built and security-hardened; pre-revenue. See [`docs/product-roadmap.md`](docs/product-roadmap.md) (v2.0) for the authoritative status and next milestone (Phase 6 — first paying customers).

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
# For production: set ENVIRONMENT=production, a strong JWT_SECRET, and ENCRYPTION_KEY
# (the app refuses to boot in production without them)

# 2. Start all services
docker compose up --build

# 3. Seed demo data
docker compose exec backend python -m app.seed.seed_data

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Tests

```bash
cd backend
python -m pytest tests/   # 62 tests; SQLite in-memory, no Docker needed
```

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@reputationos.ai | demo1234 |
| Agency Admin | agency@stellar.digital | demo1234 |
| Client Admin | manager@tastyburger.com | demo1234 |
| Marketing | marketing@tastyburger.com | demo1234 |

## Tech Stack

- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Recharts, Zustand
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy (async), Alembic
- **AI**: Groq (`openai/gpt-oss-120b`)
- **Database**: PostgreSQL 16
- **Infrastructure**: Docker Compose

## Documentation

| Doc | Purpose |
|---|---|
| [`docs/product-roadmap.md`](docs/product-roadmap.md) | Authoritative status, phases, KPI scoreboard |
| [`docs/knowledge-graph.md`](docs/knowledge-graph.md) | Architecture, flows, project structure |
| [`docs/product.md`](docs/product.md) | Full feature and API reference |
| [`docs/security-privacy.md`](docs/security-privacy.md) | Security controls and known gaps |
