# Baserow backend 2.4.3 (official image, unmodified) with a Railway start script:
# Postgres wait, migrations, Bucket CORS and a first admin created before the API
# listens. Premium/enterprise code in the image stays unloaded with BASEROW_OSS_ONLY.
ARG BASEROW_BACKEND_IMAGE=baserow/backend:2.4.3@sha256:52d77853dca3d533d1e5514b37adc763908486e74fa3ae0b35238c72658eb4c1
FROM ${BASEROW_BACKEND_IMAGE}

COPY --chmod=0755 railway-backend.sh /railway/railway-backend.sh
COPY --chmod=0755 railway_baserow.py /railway/railway_baserow.py

ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/railway/railway-backend.sh"]
CMD []
