#!/usr/bin/env sh
# Restore a ReputationOS PostgreSQL backup produced by backup_db.sh.
#
# Usage: ./scripts/restore_db.sh backups/reputationos_20260705_020000.dump
#
# DESTRUCTIVE: drops and recreates the application schema in the target
# database. Stop the backend first so nothing writes mid-restore:
#   docker compose -f docker-compose.prod.yml stop backend
set -eu

DUMP_FILE="${1:?usage: restore_db.sh <dump-file>}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

[ -s "$DUMP_FILE" ] || { echo "ERROR: dump file missing or empty: $DUMP_FILE" >&2; exit 1; }

printf 'This will OVERWRITE the current database with %s. Type yes to continue: ' "$DUMP_FILE"
read -r answer
[ "$answer" = "yes" ] || { echo "aborted"; exit 1; }

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < "$DUMP_FILE"

echo "Restore complete. Restart the backend:"
echo "  docker compose -f $COMPOSE_FILE start backend"
