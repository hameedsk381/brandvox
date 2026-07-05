#!/usr/bin/env sh
# Nightly PostgreSQL backup for ReputationOS.
#
# Usage:   ./scripts/backup_db.sh [backup_dir]
# Cron:    0 2 * * * /opt/brandvox/scripts/backup_db.sh /var/backups/reputationos
#
# Dumps the compose postgres service with pg_dump (custom format, compressed)
# and keeps the most recent $RETAIN_DAYS days of backups.
set -eu

BACKUP_DIR="${1:-./backups}"
RETAIN_DAYS="${RETAIN_DAYS:-14}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
STAMP=$(date +%Y%m%d_%H%M%S)
OUT="$BACKUP_DIR/reputationos_$STAMP.dump"

mkdir -p "$BACKUP_DIR"

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$OUT"

# A zero-byte dump means the exec silently failed; treat as error.
[ -s "$OUT" ] || { echo "ERROR: backup file is empty: $OUT" >&2; rm -f "$OUT"; exit 1; }

find "$BACKUP_DIR" -name 'reputationos_*.dump' -mtime +"$RETAIN_DAYS" -delete

echo "OK: $(du -h "$OUT" | cut -f1) written to $OUT"
