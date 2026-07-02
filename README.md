# ReputationOS AI

AI-Powered Brand Reputation Intelligence Platform — POC

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 2. Start all services
docker compose up --build

# 3. Seed demo data
docker compose exec backend python -m app.seed.seed_data

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
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
- **Backend**: FastAPI, Python 3.12, SQLAlchemy, Alembic
- **AI**: Groq (Llama 3.3 70B)
- **Database**: PostgreSQL 16
- **Infrastructure**: Docker Compose
