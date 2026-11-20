#!/bin/bash
# Railway start script for the Baserow backend (API server). Order:
#   1. sane defaults for values that would otherwise stop the start,
#   2. wait for Postgres, apply migrations (upstream's locked_migrate),
#   3. Bucket CORS, first admin account (empty database only),
#   4. upstream docker-entrypoint.sh gunicorn, with migrations already done.
# Celery services run the upstream entrypoint directly (see template.json).
set -euo pipefail

ENTRY=/baserow/backend/docker/docker-entrypoint.sh
HELPER=/railway/railway_baserow.py
source /baserow/venv/bin/activate

case "${BASEROW_PUBLIC_URL:-}" in
  http://*|https://*) ;;
  *)
    if [[ -n "${RAILWAY_PUBLIC_DOMAIN:-}" ]]; then
      echo "[railway] WARNING: BASEROW_PUBLIC_URL is not an http(s) URL; using https://$RAILWAY_PUBLIC_DOMAIN"
      export BASEROW_PUBLIC_URL="https://$RAILWAY_PUBLIC_DOMAIN"
    fi
    ;;
esac

if [[ ! "${BASEROW_BACKEND_PORT:-8000}" =~ ^[0-9]+$ ]]; then
  echo "[railway] WARNING: BASEROW_BACKEND_PORT is not a number; using 8000"
  export BASEROW_BACKEND_PORT=8000
fi
if [[ ! "${BASEROW_AMOUNT_OF_GUNICORN_WORKERS:-2}" =~ ^[1-9][0-9]*$ ]]; then
  echo "[railway] WARNING: BASEROW_AMOUNT_OF_GUNICORN_WORKERS is not a positive number; using 2"
  export BASEROW_AMOUNT_OF_GUNICORN_WORKERS=2
fi
python "$HELPER" wait-db

if [[ "${MIGRATE_ON_STARTUP:-true}" == "true" ]]; then
  echo "[railway] applying migrations (the first start takes a few minutes)"
  OTEL_SERVICE_NAME=backend-migrate python /baserow/backend/src/baserow/manage.py locked_migrate
fi

python "$HELPER" bucket-cors || echo "[railway] WARNING: bucket CORS step failed; continuing"
python "$HELPER" admin

export MIGRATE_ON_STARTUP=false
exec /bin/bash "$ENTRY" gunicorn
