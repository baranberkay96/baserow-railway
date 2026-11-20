# Baserow 2.4 No-Code Database (Postgres, Redis, Celery, S3): composer spec

Listing name: **Baserow 2.4 No-Code Database (Postgres, Redis, Celery, S3)**
Description (71 chars): Open-source Airtable alternative: API, Celery workers and Bucket files.
Category: Other. Icon: `https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/baserow.svg`
Repository: `baranberkay96/baserow-railway` (this folder is the repo root).

## Services

| Service | Source | Start | Public | Healthcheck |
|---|---|---|---|---|
| Baserow (gateway) | repo `/services/gateway` (`caddy:2.11.9-alpine@sha256:003a9780…f0`) | `caddy run` | domain → 8080 | `/_gateway/health`, 300 s |
| Backend | repo `/services/backend` (`FROM baserow/backend:2.4.3@sha256:52d77853…b4c1`, released 2026-11-14) | `railway-backend.sh` → upstream `gunicorn` (uvicorn workers) on `[::]:8000` | no | `/api/_health/`, 1200 s |
| Frontend | `baserow/web-frontend:2.4.3@sha256:6f64f079…2092` | image entrypoint (Nitro on `::`:3000) | no | `/_health/`, 600 s |
| Celery Worker | `baserow/backend:2.4.3` (same digest) | `tini -- bash docker-entrypoint.sh celery-worker` | no | — |
| Export Worker | same image | `… celery-exportworker` | no | — |
| Celery Beat | same image | `… celery-beat` | no | — |
| Postgres | `ghcr.io/railwayapp-templates/postgres-ssl:18.6@sha256:4fc833b4…c863` (pgvector available) | — | no | volume `/var/lib/postgresql/data` |
| Redis | `redis:8.2.11@sha256:b0b01167…c8d` | — | no | volume `/data` |
| Bucket | Railway Bucket `Bucket` | — | — | — |

All app services restart ALWAYS (Postgres/Redis may start later, STANDARD 8.5). Celery services reference the Backend's variables (`${{Backend.X}}`), so secrets, database, Redis, Bucket and e-mail settings are edited in one place.

## Design

- **Multi-service, as upstream's `docker-compose.yml`** rather than the all-in-one image the market leader uses: workers and the API scale and restart independently, and memory per service stays well under the Trial cap.
- **No shared volume**: upstream shares a `media` volume between backend and workers; Railway volumes cannot be shared, so all file storage goes to the Railway Bucket via django-storages (`AWS_*`): private ACL, signed URLs valid 24 h, virtual-hosted style. The backend sets the Bucket CORS rule (GET/HEAD from `BASEROW_PUBLIC_URL`) with boto3 on each start.
- **Gateway** reproduces upstream's Caddy routing without TLS (Railway terminates it) and without local media.
- **Backend start** (`railway-backend.sh`): fallback for a non-URL `BASEROW_PUBLIC_URL`, port and worker count; Postgres wait (15 min); `locked_migrate`; Bucket CORS; first admin via `UserHandler.create_user` + `is_staff`, then `allow_new_signups=false` (once, empty database only); `BASEROW_ADMIN_RESET_PASSWORD` support; then upstream `gunicorn` with `MIGRATE_ON_STARTUP=false`. Invalid admin e-mail → `admin@example.com`; password outside 8-256 → random password nobody knows + log hint (fail closed, deploy still succeeds).
- **Open-source edition only**: `BASEROW_OSS_ONLY=true` on backend, workers and frontend.
- **Concurrency**: `BASEROW_AMOUNT_OF_WORKERS=1` (Celery would otherwise size from the host's CPU count), 2 gunicorn workers.
- `BASEROW_EXTRA_ALLOWED_HOSTS` includes the private name (frontend SSR) and `healthcheck.railway.app`.

## Improvements over market templates

Market (2026-11): leader 523 active on `baserow/baserow:2.0.0` all-in-one (+ Postgres 17, Redis 8.2.1), healthcheck empty, no Bucket (files on the container volume), open sign-up with first-come admin, premium/enterprise code loaded. Others: all-in-one 2.3.3 without Redis; a 0-active fork with an admin bootstrap.

- Baserow 2.4.3 (current) pinned by digest; Postgres 18 with pgvector.
- Upstream multi-service layout with dedicated export worker and beat scheduler.
- Files in a private Railway Bucket with signed URLs and automatic CORS.
- Admin created before the API listens; sign-up closed afterwards.
- MIT edition only, as stated in the listing.

## Resources

RESOURCES_TABLE

## Verification checklist

1. All 8 services SUCCESS; gateway `/_gateway/health` 200; `/api/_health/` 200 through the gateway.
2. Backend log: migrations, `bucket CORS allows …`, `first admin … created; new sign-ups off`.
3. Login via `POST /api/user/token-auth/` with the generated credentials → 200; wrong password → 401; stranger sign-up → rejected.
4. Create a database and table, add rows, upload a file to a file field; the returned thumbnail/file URL is a signed Bucket URL that downloads (and passes CORS from the public origin).
5. Export the table as CSV (export worker) and download it from the Bucket.
6. `GET /api/_health/full/` as admin: all checks passing.
7. Fresh deploy with odd values (`BASEROW_ADMIN_PASSWORD=abc`, `BASEROW_ADMIN_EMAIL=bad`, `BASEROW_PUBLIC_URL=nonsense`) → SUCCESS with warnings.

## Open questions

- Upgrading from the market's all-in-one template to this layout needs a database dump/restore and moving files to the Bucket; not covered.
