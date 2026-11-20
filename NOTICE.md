# Notice

This package deploys **Baserow** by Baserow B.V. (https://github.com/baserow/baserow) using the official images `baserow/backend:2.4.3` and `baserow/web-frontend:2.4.3`, pinned by digest and used unmodified as bases.

## Licensing (checked 2026-11-20, tag 2.4.3)

- Baserow Open Source Edition (everything outside `premium/` and `enterprise/`, plus all client-side JavaScript) is licensed under the MIT Expat license, Copyright (c) 2019-present Baserow B.V.
- `premium/` and `enterprise/` are under Baserow's commercial licenses, which allow production use only with a paid subscription. The official images contain that code. This template sets `BASEROW_OSS_ONLY=true` on the backend, Celery services and frontend, so those modules are not loaded and only the MIT edition runs. Removing that variable loads them; using them in production then needs a Baserow licence.
- The images are pulled from Baserow's own Docker Hub repositories; this repository does not redistribute Baserow code.

## What is used and how

- Service layout, commands and variables follow upstream `docker-compose.yml`, `Caddyfile`, `backend/docker/docker-entrypoint.sh` and `web-frontend/docker/docker-entrypoint-prod.sh` at tag `2.4.3`.
- `services/gateway/Caddyfile` is original; its routing reproduces upstream's Caddyfile (backend paths `/api`, `/ws`, `/mcp`, `/assistant`).
- `services/backend/railway-backend.sh` and `railway_baserow.py` are original; they call upstream's `locked_migrate` command, `UserHandler.create_user` and the upstream entrypoint.
- Base images: `caddy:2.11.9-alpine` (Apache-2.0), Railway's `postgres-ssl` and Redis templates.
- Icon: Dashboard Icons by homarr-labs (https://github.com/homarr-labs/dashboard-icons).

Market templates were read for comparison only; no files or text were copied. README and docs text are original.

This is a community template and is not affiliated with or endorsed by Baserow B.V.
