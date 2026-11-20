# Deploy and Host Baserow with Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/baserow-24-no-code-database-postgres-red?referralCode=20H68q)

Baserow is an open-source no-code database and Airtable alternative: build tables, views, forms and apps on top of PostgreSQL, with a REST API and real-time collaboration. This template runs Baserow 2.4 as separate services (API, web frontend, Celery workers, scheduler and gateway) with PostgreSQL 18, Redis and a Railway Bucket for files.

## About Hosting Baserow

Baserow's official multi-service layout splits work across a Django API, a Nuxt web frontend, two Celery workers (fast jobs and slow exports or imports), a Celery beat scheduler and a Caddy gateway. They share PostgreSQL, Redis and a file store. Upstream uses a shared Docker volume for files; Railway volumes cannot be shared between services, so this template stores uploads, thumbnails and exports in a private Railway Bucket and serves them through signed URLs.

The backend start script waits for Postgres, runs migrations, sets the Bucket's CORS rule and creates the first admin before the API accepts requests, then closes public sign-up. Only the MIT-licensed open-source edition is loaded (`BASEROW_OSS_ONLY`).

## Common Use Cases

- Replace Airtable or spreadsheets with a shared database your team can edit
- Collect data with forms and publish it in grid, gallery, kanban or calendar views
- Build internal tools and portals with the application builder
- Feed other apps through Baserow's REST API and webhooks

## Dependencies for Baserow Hosting

- Baserow 2.4.3 backend and web-frontend images (pinned by digest)
- Caddy 2.11 gateway
- PostgreSQL 18 with pgvector (Railway's `postgres-ssl` image)
- Redis 8.2
- A Railway Bucket for files

### Deployment Dependencies

- Baserow source: https://github.com/baserow/baserow
- Docker Compose install guide: https://baserow.io/docs/installation/install-with-docker-compose
- Configuration reference: https://baserow.io/docs/installation/configuration
- Railway Buckets: https://docs.railway.com/guides/storage-buckets

### Implementation Details

| Service | What it does | Public |
|---|---|---|
| Baserow | Caddy gateway: `/api`, `/ws`, `/mcp`, `/assistant` to Backend, the rest to Frontend | yes |
| Backend | Django API (gunicorn + uvicorn), migrations and first admin on start | no |
| Frontend | Nuxt web app (server-side rendering) | no |
| Celery Worker | Realtime updates, webhooks, automations, formula updates | no |
| Export Worker | Exports, imports, duplication, trash cleanup | no |
| Celery Beat | Periodic jobs | no |
| Postgres | All data (pgvector enabled) | no |
| Redis | Cache, websockets, Celery broker | no |
| Bucket | Uploaded files, thumbnails, exports (private, signed URLs) | no |

**First login**

1. Wait for the first deploy; the backend migrates a new database in a few minutes.
2. Open the **Baserow** service's public URL and log in with `BASEROW_ADMIN_EMAIL` (default `admin@example.com`) and the generated `BASEROW_ADMIN_PASSWORD` from the **Backend** service's Variables tab.
3. Change your e-mail and password in account settings.

**Adding people.** Public sign-up is turned off once, at the first start (`BASEROW_ALLOW_NEW_SIGNUPS=false`). Invite people to a workspace; invited addresses can still create accounts. Invitation e-mails need SMTP (`EMAIL_SMTP=true` plus `EMAIL_SMTP_*`, Railway Pro for outbound SMTP). Without SMTP, open sign-up for a moment in Admin > Settings.

**Custom domain.** Add it to the Baserow service and set `BASEROW_PUBLIC_URL` on the Backend service to `https://{your-domain}`; the other services reference it. Redeploy all services.

**Scaling.** Raise `BASEROW_AMOUNT_OF_GUNICORN_WORKERS` on Backend for more API throughput, `BASEROW_AMOUNT_OF_WORKERS` for Celery concurrency, or add replicas to Celery Worker and Export Worker. Keep Celery Beat at one replica.

**Versions.** Images are pinned by tag and digest: the backend in `services/backend/Dockerfile`, the frontend and Celery services in the template. To upgrade, move all of them to the same new 2.x release, back up Postgres, and redeploy; migrations run on start.

**Lost admin password.** Set a new `BASEROW_ADMIN_PASSWORD` and `BASEROW_ADMIN_RESET_PASSWORD=true` on Backend, redeploy, then set it back to `false`.

**Resources.** Measured idle on Railway after a test workload: Backend 0.42 GB, Export Worker 0.36 GB, Celery Worker 0.28 GB, Celery Beat 0.24 GB, Frontend 0.18 GB, Postgres 0.11 GB, Redis 0.03 GB, gateway 0.01 GB; about 1.6 GB in total and near-zero idle CPU, roughly $17-22 per month. Every service fits the Trial plan's 1 GB limit; Hobby is recommended.

**License.** Baserow's open-source edition is MIT. The official images also contain premium and enterprise code under Baserow's commercial license; with `BASEROW_OSS_ONLY=true` that code is not loaded. This is a community template; it is not affiliated with Baserow B.V.

### Why Deploy Baserow on Railway?

Railway runs every Baserow process, the database, Redis and file storage in one project with private networking and HTTPS. You get the production layout upstream recommends without managing servers, and you can scale workers or add a domain from the dashboard.
