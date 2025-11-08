import os
from pathlib import Path
from datetime import timedelta


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-secret")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ['*']

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # pode deixar [] se não tiver pasta templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "django_celery_beat",
    "authentication",
    "coins",
    "portfolio",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application" if (BASE_DIR / "core/asgi.py").exists() else None

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "CryptoTracker API",
    "DESCRIPTION": "API do desafio",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --------- DB: parse DATABASE_URL ----------
# Formato esperado: postgresql://user:pass@host:port/db
from urllib.parse import urlparse
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:crypto_password@postgres:5432/postgresdb")
u = urlparse(db_url)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": u.path.lstrip("/"),
        "USER": u.username,
        "PASSWORD": u.password,
        "HOST": u.hostname,
        "PORT": u.port or "5432",
    }
}

# Redis / Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://redis:6379/0"))
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://redis:6379/0"))
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    "update-coin-prices-cache": {
        "task": "coins.tasks.update_coin_prices_cache",
        "schedule": 120.0,  # a cada 2 min
    },
    "check-price-alerts": {
        "task": "portfolio.tasks.check_price_alerts",
        "schedule": 300.0,  # a cada 5 min
    },
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

AUTH_USER_MODEL = "authentication.User"

COINGECKO_API_URL = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
COINGECKO_KEY = os.getenv("COINGECKO_KEY", "")

# Opcional (não recomendado): usar query string no lugar do header
COINGECKO_KEY_IN_QUERY = os.getenv("COINGECKO_KEY_IN_QUERY", "0")

# Resiliência cliente HTTP
COINGECKO_TIMEOUT = os.getenv("COINGECKO_TIMEOUT", "10")        # segundos
COINGECKO_MAX_RETRIES = os.getenv("COINGECKO_MAX_RETRIES", "3")
COINGECKO_BACKOFF_BASE = os.getenv("COINGECKO_BACKOFF_BASE", "0.7")

# TTLs de cache (se quiser usar nas views)
COIN_LIST_CACHE_TTL = int(os.getenv("COIN_LIST_CACHE_TTL", "120"))
COIN_DETAIL_CACHE_TTL = int(os.getenv("COIN_DETAIL_CACHE_TTL", "300"))
COIN_CHART_CACHE_TTL = int(os.getenv("COIN_CHART_CACHE_TTL", "300"))