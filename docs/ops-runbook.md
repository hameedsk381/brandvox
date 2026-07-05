# Operations Runbook

> Closes the roadmap Phase 4 open item "backup and restore process".
> Scope: single-box Docker Compose production deployment (the Phase 6 pilot footprint).

## 1. Production deployment

```sh
cp .env.example .env        # then fill in REAL values (see below)
docker compose -f docker-compose.prod.yml up -d --build
```

The prod compose file (`docker-compose.prod.yml`) differs from the dev one:

- `ENVIRONMENT=production` — backend refuses to boot with a default `JWT_SECRET`, missing `ENCRYPTION_KEY`, or `DEMO_MODE=true`
- runs `alembic upgrade head` before serving (Alembic is the sole schema authority in production)
- no source mounts, no `--reload`, `restart: unless-stopped`
- postgres has **no host port** — reachable only inside the compose network

Required `.env` values (compose fails fast if missing): `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `JWT_SECRET` (long random string), `ENCRYPTION_KEY` (Fernet key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`), `GROQ_API_KEY`, `BACKEND_URL`, `FRONTEND_URL`, `BACKEND_CORS_ORIGINS`.

## 2. Backups

**Cadence: nightly, retained 14 days.** Script: [scripts/backup_db.sh](../scripts/backup_db.sh) — `pg_dump` custom format, compressed, with empty-file detection and automatic rotation.

```sh
# manual run
./scripts/backup_db.sh /var/backups/reputationos

# cron (Linux host) — 02:00 daily
0 2 * * * cd /opt/brandvox && ./scripts/backup_db.sh /var/backups/reputationos >> /var/log/reputationos-backup.log 2>&1
```

On a Windows host use Task Scheduler with `bash scripts/backup_db.sh D:\backups\reputationos` (Git Bash) at the same cadence.

**Off-box copy:** backups on the same disk as the database protect against nothing but fat fingers. Sync the backup dir to object storage or another machine (e.g. `rclone sync /var/backups/reputationos remote:reputationos-backups` as a second cron entry). Backups contain review data and encrypted OAuth tokens — treat them as sensitive; the Fernet `ENCRYPTION_KEY` must be escrowed separately (password manager), because a restored database is unreadable without the same key.

## 3. Restore

Script: [scripts/restore_db.sh](../scripts/restore_db.sh) — destructive, asks for confirmation.

```sh
docker compose -f docker-compose.prod.yml stop backend
./scripts/restore_db.sh /var/backups/reputationos/reputationos_YYYYMMDD_HHMMSS.dump
docker compose -f docker-compose.prod.yml start backend
```

## 4. Restore drill (do this before the first paying customer)

Run quarterly; record the date and outcome in the table below.

1. Take a fresh backup with `backup_db.sh`.
2. Spin up a scratch postgres: `docker run -d --name restore-drill -e POSTGRES_USER=repuser -e POSTGRES_PASSWORD=x -e POSTGRES_DB=reputationos postgres:16-alpine`
3. `docker exec -i restore-drill pg_restore -U repuser -d reputationos --no-owner < <dump-file>`
4. Verify: `docker exec restore-drill psql -U repuser -d reputationos -c "select count(*) from reviews; select count(*) from agencies;"` — counts should match production.
5. `docker rm -f restore-drill`

| Date | Dump tested | Result | Notes |
|---|---|---|---|
| _none yet_ | | | first drill due before first paying customer |

## 5. Health monitoring

- `GET /api/health` — liveness
- Scheduler health: see scheduler health endpoint (`app/core/scheduler.py`); hourly `sync_google_reviews` job is the critical one
- Sync failures surface per-integration via `last_sync_status` / `last_sync_error` (integrations UI shows banners) and fire AlertIntegration webhooks (Slack/Teams/Email)
- Activation KPIs for the pilot scoreboard: `GET /api/analytics/activation`

## 6. Rotation / incident notes

- **JWT_SECRET rotation** invalidates all sessions (users re-login). Safe any time outside a demo.
- **ENCRYPTION_KEY** cannot be rotated by simply swapping the value — existing tokens become unreadable and every agency must reconnect Google. If the key leaks, rotate it, accept the mass-reconnect, and notify affected agencies.
- If Google sync fails repeatedly for one agency, check quota first (each agency's Google Cloud project has GBP quota 0 until approved — see onboarding runbook).
