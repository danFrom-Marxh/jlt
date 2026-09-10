"""Django settings for Just Like That.

Development works with SQLite/local media by default. Production can switch to
Render Postgres and Cloudflare R2 entirely through environment variables.
"""
from pathlib import Path
import os

import dj_database_url
import environ
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


# Core / security
SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-before-production")
# DEBUG = env.bool("DEBUG", default=True)
DEBUG = True

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost", "192.168.1.72"],
)
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
if RENDER_EXTERNAL_HOSTNAME:
    render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

OPENWEATHERMAP_API_KEY = env("OPENWEATHERMAP_API_KEY", default="")


# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    "heart",
    "crispy_forms",
    "crispy_bootstrap4",
    "storages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "just_like_that.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "heart.context_processors.store_context",
            ],
        },
    },
]

WSGI_APPLICATION = "just_like_that.wsgi.application"
ASGI_APPLICATION = "just_like_that.asgi.application"


# Database: SQLite locally, DATABASE_URL (Render Postgres) in production.
DATABASE_URL = env("DATABASE_URL", default="").strip()
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True


# Static files are built once and served by WhiteNoise.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media are local in development and can be stored on Cloudflare R2 in production.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

USE_CLOUDFLARE_R2 = env.bool("USE_CLOUDFLARE_R2", default=False)
if USE_CLOUDFLARE_R2:
    r2_account_id = env("CLOUDFLARE_R2_ACCOUNT_ID", default="").strip()
    r2_access_key = env("CLOUDFLARE_R2_ACCESS_KEY_ID", default="").strip()
    r2_secret_key = env("CLOUDFLARE_R2_SECRET_ACCESS_KEY", default="").strip()
    r2_bucket = env("CLOUDFLARE_R2_BUCKET_NAME", default="").strip()
    r2_custom_domain = env("CLOUDFLARE_R2_CUSTOM_DOMAIN", default="").strip()

    missing = [
        name
        for name, value in {
            "CLOUDFLARE_R2_ACCOUNT_ID": r2_account_id,
            "CLOUDFLARE_R2_ACCESS_KEY_ID": r2_access_key,
            "CLOUDFLARE_R2_SECRET_ACCESS_KEY": r2_secret_key,
            "CLOUDFLARE_R2_BUCKET_NAME": r2_bucket,
        }.items()
        if not value
    ]
    if missing:
        raise ImproperlyConfigured(
            "Cloudflare R2 est activé mais ces variables manquent : " + ", ".join(missing)
        )

    if r2_custom_domain:
        r2_custom_domain = r2_custom_domain.removeprefix("https://").removeprefix("http://").rstrip("/")

    r2_options = {
        "access_key": r2_access_key,
        "secret_key": r2_secret_key,
        "bucket_name": r2_bucket,
        "endpoint_url": f"https://{r2_account_id}.r2.cloudflarestorage.com",
        "region_name": "auto",
        "default_acl": None,
        "file_overwrite": False,
        "object_parameters": {"CacheControl": "public, max-age=31536000, immutable"},
    }
    if r2_custom_domain:
        # A Cloudflare custom domain makes media URLs stable and cacheable.
        r2_options["custom_domain"] = r2_custom_domain
        r2_options["querystring_auth"] = False

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": r2_options,
    }


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CRISPY_TEMPLATE_PACK = "bootstrap4"


# Store / homepage
STORE_NAME = env("STORE_NAME", default="Just Like That")
STORE_CURRENCY_SYMBOL = env("STORE_CURRENCY_SYMBOL", default="€")
STORE_ADDRESS = env("STORE_ADDRESS", default="").strip()
SITE_DESCRIPTION = env(
    "SITE_DESCRIPTION",
    default="Just Like That : une sélection de produits utiles, élégants et simples à commander, avec paiement sécurisé.",
).strip()
SUPPORT_EMAIL = env("SUPPORT_EMAIL", default="").strip()
GOOGLE_MAPS_EMBED_API_KEY = env("GOOGLE_MAPS_EMBED_API_KEY", default="").strip()
NEWSLETTER_PROMO_CODE = env("NEWSLETTER_PROMO_CODE", default="JLT8").strip().upper() or "JLT8"


# Stripe
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_CURRENCY = env("STRIPE_CURRENCY", default="eur").lower()
STRIPE_SHIPPING_COUNTRIES = [
    country.strip().upper()
    for country in env(
        "STRIPE_SHIPPING_COUNTRIES",
        default="FR,BE,CA,US,GB,DE,ES,IT,ML,SN,CI,GA",
    ).split(",")
    if country.strip()
]


# Transactional e-mail / receipts. In production, configure a Gmail App Password.
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com").strip()
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="").strip()
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="").strip()
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=15)
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default=EMAIL_HOST_USER or f"{STORE_NAME} <noreply@localhost>",
).strip()
if not SUPPORT_EMAIL:
    SUPPORT_EMAIL = DEFAULT_FROM_EMAIL
SEND_ORDER_RECEIPTS = env.bool("SEND_ORDER_RECEIPTS", default=True)
if not DEBUG and SEND_ORDER_RECEIPTS and (not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD):
    raise ImproperlyConfigured(
        "Les reçus e-mail sont activés en production mais EMAIL_HOST_USER / "
        "EMAIL_HOST_PASSWORD ne sont pas configurés."
    )
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
    else "django.core.mail.backends.console.EmailBackend"
)

# WhiteNoise can cache hashed static assets aggressively.
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0
