import os

from .base import *  # noqa

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True

# ---- Hosting (Render + Neon) ----
from urllib.parse import urlparse, unquote  # noqa: E402

_db = os.getenv("DATABASE_URL", "")
if _db:  # one connection string, e.g. from Neon
    _u = urlparse(_db)
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _u.path.lstrip("/"), "USER": unquote(_u.username or ""), "PASSWORD": unquote(_u.password or ""),
        "HOST": _u.hostname, "PORT": str(_u.port or 5432),
        "OPTIONS": {"sslmode": "require"}, "CONN_MAX_AGE": 60,
    }}

# Static files (admin, API docs) served by WhiteNoise
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# The Render health check calls over plain HTTP inside the platform
SECURE_REDIRECT_EXEMPT = [r"^api/v1/health/$"]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]
