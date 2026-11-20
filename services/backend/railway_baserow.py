"""Railway helpers for the Baserow backend image. Never prints secret values.

    python railway_baserow.py wait-db      # wait until Postgres accepts connections
    python railway_baserow.py bucket-cors  # let browsers read files from the Railway Bucket
    python railway_baserow.py admin        # first staff account + sign-up policy (empty DB only)
"""
import os
import re
import secrets
import sys
import time

EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def log(msg):
    print(f"[railway] {msg}", flush=True)


def warn(msg):
    print(f"[railway] WARNING: {msg}", flush=True)


def wait_db():
    import psycopg

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        warn("DATABASE_URL is empty; Baserow falls back to DATABASE_* variables")
        return
    deadline = time.time() + 900
    attempt = 0
    while True:
        attempt += 1
        try:
            with psycopg.connect(url, connect_timeout=5) as conn:
                conn.execute("select 1")
            log("Postgres is reachable")
            return
        except Exception as error:  # noqa: BLE001 - any failure means "not ready yet"
            if time.time() > deadline:
                raise SystemExit(f"[railway] ERROR: Postgres unreachable for 15 minutes: {type(error).__name__}")
            if attempt == 1 or attempt % 6 == 0:
                log(f"waiting for Postgres ({type(error).__name__})")
            time.sleep(5)


def bucket_cors():
    env = os.environ
    bucket = env.get("AWS_STORAGE_BUCKET_NAME", "")
    if not bucket or not env.get("AWS_ACCESS_KEY_ID") or not env.get("AWS_SECRET_ACCESS_KEY"):
        log("Bucket not configured: files are stored on the local disk of the backend")
        return
    if env.get("BASEROW_BUCKET_CORS", "true").lower() == "false":
        log("BASEROW_BUCKET_CORS=false: bucket CORS left unchanged")
        return
    from urllib.parse import urlparse

    origins = []
    for value in [env.get("BASEROW_PUBLIC_URL", "")] + env.get("BASEROW_EXTRA_PUBLIC_URLS", "").split(","):
        parsed = urlparse(value.strip())
        if parsed.scheme in ("http", "https") and parsed.netloc:
            origins.append(f"{parsed.scheme}://{parsed.netloc}")
    origins = sorted(set(origins))
    if not origins:
        warn("no valid BASEROW_PUBLIC_URL; bucket CORS not set")
        return
    import boto3
    from botocore.config import Config

    client = boto3.client(
        "s3",
        endpoint_url=env.get("AWS_S3_ENDPOINT_URL") or None,
        region_name=env.get("AWS_S3_REGION_NAME") or "us-east-1",
        aws_access_key_id=env["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=env["AWS_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4", s3={"addressing_style": env.get("AWS_S3_ADDRESSING_STYLE") or "virtual"}),
    )
    rule = {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": origins,
        "ExposeHeaders": ["Content-Length", "Content-Type", "Content-Disposition", "ETag"],
        "MaxAgeSeconds": 3600,
    }
    for attempt in range(1, 6):
        try:
            client.put_bucket_cors(Bucket=bucket, CORSConfiguration={"CORSRules": [rule]})
            log(f"bucket CORS allows {', '.join(origins)}")
            return
        except Exception as error:  # noqa: BLE001
            warn(f"bucket CORS attempt {attempt}/5 failed: {type(error).__name__}: {str(error)[:200]}")
            time.sleep(3 * attempt)
    warn("bucket CORS not set; file previews may fail until the next restart")


def admin():
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baserow.config.settings.base")
    django.setup()
    from django.contrib.auth import get_user_model
    from django.db import transaction

    from baserow.core.handler import CoreHandler
    from baserow.core.user.handler import UserHandler

    User = get_user_model()
    if User.objects.exists():
        log("Baserow already has accounts: first-admin bootstrap skipped")
        return
    email = os.environ.get("BASEROW_ADMIN_EMAIL", "").strip().lower()
    if not email:
        warn("BASEROW_ADMIN_EMAIL is empty; the first person to sign up becomes the admin. Set it and redeploy to close that window.")
        return
    if not EMAIL.match(email):
        warn("BASEROW_ADMIN_EMAIL is not a valid e-mail; using admin@example.com. Change it later in your account settings.")
        email = "admin@example.com"
    password = os.environ.get("BASEROW_ADMIN_PASSWORD", "")
    locked = False
    if not 8 <= len(password) <= 256:
        warn(
            "BASEROW_ADMIN_PASSWORD must be 8-256 characters; the admin is created with a random password nobody knows. "
            "Set a valid BASEROW_ADMIN_PASSWORD and BASEROW_ADMIN_RESET_PASSWORD=true, then redeploy the Backend."
        )
        password = secrets.token_urlsafe(32)
        locked = True
    name = os.environ.get("BASEROW_ADMIN_NAME", "").strip() or "Admin"
    with transaction.atomic():
        user = UserHandler().create_user(name, email, password)
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=["is_staff"])
        allow = os.environ.get("BASEROW_ALLOW_NEW_SIGNUPS", "false").strip().lower() == "true"
        settings = CoreHandler().get_settings()
        settings.allow_new_signups = allow
        settings.save(update_fields=["allow_new_signups"])
    log(f"first admin {email} created{' (locked, see warning above)' if locked else ''}; new sign-ups {'allowed' if allow else 'off (invitations still work)'}")


def reset_password():
    if os.environ.get("BASEROW_ADMIN_RESET_PASSWORD", "false").strip().lower() != "true":
        return
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baserow.config.settings.base")
    django.setup()
    from django.contrib.auth import get_user_model

    email = os.environ.get("BASEROW_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("BASEROW_ADMIN_PASSWORD", "")
    if not 8 <= len(password) <= 256:
        warn("BASEROW_ADMIN_RESET_PASSWORD=true but BASEROW_ADMIN_PASSWORD is not 8-256 characters; nothing changed")
        return
    user = get_user_model().objects.filter(email__iexact=email).first()
    if not user:
        warn(f"BASEROW_ADMIN_RESET_PASSWORD=true but no account {email} exists; nothing changed")
        return
    user.set_password(password)
    user.save(update_fields=["password"])
    log(f"password of {email} set from BASEROW_ADMIN_PASSWORD; set BASEROW_ADMIN_RESET_PASSWORD back to false")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "wait-db":
        wait_db()
    elif command == "bucket-cors":
        bucket_cors()
    elif command == "admin":
        admin()
        reset_password()
    else:
        raise SystemExit(__doc__)
