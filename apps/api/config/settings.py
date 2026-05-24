import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

_DEBUG_RAW = os.environ.get("DEBUG", "True").lower() in ["true", "1", "yes"]
DEBUG = _DEBUG_RAW

_SECRET_DEFAULT = "django-insecure-default-key-for-dev"
SECRET_KEY = os.environ.get("SECRET_KEY", _SECRET_DEFAULT)
if not DEBUG and SECRET_KEY == _SECRET_DEFAULT:
    raise ImproperlyConfigured("SECRET_KEY must be set to a unique value when DEBUG=False.")

_hosts_raw = os.environ.get("ALLOWED_HOSTS", "").strip()
if _hosts_raw:
    ALLOWED_HOSTS = [h.strip() for h in _hosts_raw.split(",") if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
else:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set when DEBUG=False.")

OPENAPI_ENABLED = os.environ.get(
    "OPENAPI_ENABLED",
    "true" if DEBUG else "false",
).lower() in ["true", "1", "yes"]

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    'simple_history',

    # Local apps
    'core.apps.CoreConfig',
    'organization',
    'employees',
    'attendance',
    'leave',
    'shifts',
    'payroll',
    'compliance',
    'notifications',
    'recruitment',
    'wfh',
    'onboarding',
    'expenses',
    'assets',
    'helpdesk',
    'performance',
    'engagement',
    'offboarding',
    'dashboards',
    'cold_campaign',
]

PUBLIC_API_BASE_URL = os.environ.get('PUBLIC_API_BASE_URL', 'http://127.0.0.1:8000')
AI_SERVICE_BASE_URL = os.environ.get('AI_SERVICE_BASE_URL', 'http://127.0.0.1:8001')
OPENAI_DEFAULT_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-5.4-mini')
FRONTEND_APP_URL = os.environ.get('FRONTEND_APP_URL', os.environ.get('NEXT_PUBLIC_APP_URL', 'http://localhost:3000'))
CAREERS_APP_URL = os.environ.get('CAREERS_APP_URL', 'http://localhost:3001')
JOB_BOARD_CDN_URL = os.environ.get(
    'JOB_BOARD_CDN_URL',
    f"{PUBLIC_API_BASE_URL.rstrip('/')}/static/job-board",
)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@aastraahr.com')

ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.environ.get('REDIS_URL', 'redis://localhost:6379/1')],
        },
    },
}

UTIL_COOLDOWN_CPU_THRESHOLD = int(os.environ.get("UTIL_COOLDOWN_CPU_THRESHOLD", "80"))
UTIL_COOLDOWN_RAM_THRESHOLD = int(os.environ.get("UTIL_COOLDOWN_RAM_THRESHOLD", "80"))
UTIL_COOLDOWN_DURATION_SECONDS = int(os.environ.get("UTIL_COOLDOWN_DURATION_SECONDS", "300"))
UTIL_SAMPLE_INTERVAL_SECONDS = int(os.environ.get("UTIL_SAMPLE_INTERVAL_SECONDS", "30"))
UTIL_COOLDOWN_SUPER_ADMIN_BYPASS = os.environ.get(
    "UTIL_COOLDOWN_SUPER_ADMIN_BYPASS", "False"
).lower() in ["true", "1", "yes"]

METRICS_ENABLED = os.environ.get("METRICS_ENABLED", "True").lower() in ["true", "1", "yes"]
METRICS_RETENTION_HOURS = int(os.environ.get("METRICS_RETENTION_HOURS", "72"))
LOG_SOURCE = os.environ.get("LOG_SOURCE", "auto")
LOG_DOCKER_COMPOSE_PROJECT = os.environ.get("LOG_DOCKER_COMPOSE_PROJECT", "theastravision")
LOG_SERVICE_REGISTRY = {
    "api": {"docker_container": f"{LOG_DOCKER_COMPOSE_PROJECT}-api-1", "journal_unit": "aastraahr-api.service"},
    "celery-worker": {"docker_container": f"{LOG_DOCKER_COMPOSE_PROJECT}-celery-worker-1", "journal_unit": "aastraahr-celery.service"},
    "celery-beat": {"docker_container": f"{LOG_DOCKER_COMPOSE_PROJECT}-celery-beat-1", "journal_unit": "aastraahr-celery-beat.service"},
    "ai-service": {"docker_container": f"{LOG_DOCKER_COMPOSE_PROJECT}-ai-service-1", "journal_unit": "aastraahr-ai.service"},
    "admin-web": {"docker_container": f"{LOG_DOCKER_COMPOSE_PROJECT}-admin-web-1", "journal_unit": "aastraahr-web.service"},
}

CLICKHOUSE_ENABLED = os.environ.get("CLICKHOUSE_ENABLED", "False").lower() in ["true", "1", "yes"]
# When False (default), audit/platform log APIs read from PostgreSQL (SystemAuditLog, AuthSession).
# Set True only when ClickHouse is deployed; logs are mirrored asynchronously from PG writes.
CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_DATABASE = os.environ.get("CLICKHOUSE_DATABASE", "default")
CLICKHOUSE_BATCH_SIZE = int(os.environ.get("CLICKHOUSE_BATCH_SIZE", "5000"))

REDIS_ALLOW = os.environ.get("REDIS_ALLOW", "False").lower() in ("true", "1", "yes")
E2EE_ENABLED = os.environ.get("E2EE_ENABLED", "True").lower() in ("true", "1", "yes")
E2EE_SESSION_TTL_SECONDS = int(os.environ.get("E2EE_SESSION_TTL_SECONDS", "604800"))
E2EE_PUBLIC_SESSION_TTL_SECONDS = int(os.environ.get("E2EE_PUBLIC_SESSION_TTL_SECONDS", "900"))
E2EE_INTERNAL_TOKEN = os.environ.get("E2EE_INTERNAL_TOKEN", "")

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'core.middleware.cooldown_middleware.PlatformCooldownMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.timezone_middleware.TimezoneMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'core.middleware.e2ee_response_middleware.E2EEResponseMiddleware',
    'core.middleware.request_metrics_middleware.RequestMetricsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR}/db.sqlite3')
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': int(os.environ.get('PASSWORD_MIN_LENGTH', '12' if not DEBUG else '8'))},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

FRONTEND_DEBUG_LOG_PATH = Path(
    os.environ.get('FRONTEND_DEBUG_LOG_PATH', str(BASE_DIR / 'debug.log'))
)

FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('FILE_UPLOAD_MAX_MEMORY_SIZE', str(5 * 1024 * 1024)))
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', str(10 * 1024 * 1024)))

# Audit log retention (days); 0 = retain indefinitely
AUDIT_LOG_RETENTION_DAYS = int(os.environ.get('AUDIT_LOG_RETENTION_DAYS', '180'))

ALLOW_S3 = os.environ.get('ALLOW_S3', 'False').lower() in ['true', '1', 'yes']
TRACKER_ENCRYPTION_KEY = os.environ.get('TRACKER_ENCRYPTION_KEY', '')
TRACKER_MASTER_KEY = os.environ.get('TRACKER_MASTER_KEY', '')
WFH_TRACKING_ENABLED = os.environ.get('WFH_TRACKING_ENABLED', 'True').lower() in ['true', '1', 'yes']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'core.authentication.TimezoneJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.DynamicPageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['rest_framework.filters.SearchFilter', 'rest_framework.filters.OrderingFilter'],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_MINUTES', '15'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('JWT_REFRESH_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'AastraaHR API',
    'DESCRIPTION': 'Phase 1 MVP of AastraaHR',
    'VERSION': '1.0.0',
}

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
_extra_cors = os.environ.get("CORS_ALLOWED_ORIGINS", "")
for _origin in _extra_cors.split(","):
    _origin = _origin.strip()
    if _origin and _origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(_origin)
for _default_origin in (FRONTEND_APP_URL, CAREERS_APP_URL):
    if _default_origin and _default_origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(_default_origin.rstrip("/"))
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-e2ee-session",
    "x-e2ee-seq",
    "x-client-ecdh-public",
    "x-internal-service",
    "x-internal-service-token",
]

if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() in ["true", "1", "yes"]
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "True").lower() in ["true", "1", "yes"]
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    X_FRAME_OPTIONS = "DENY"

WEBAUTHN_RP_ID = os.environ.get("WEBAUTHN_RP_ID", "localhost")
WEBAUTHN_RP_NAME = os.environ.get("WEBAUTHN_RP_NAME", "AastraaHR")
WEBAUTHN_ORIGIN = os.environ.get("WEBAUTHN_ORIGIN", FRONTEND_APP_URL.rstrip("/"))

PRIVILEGED_ROLES_REQUIRE_MFA = os.environ.get(
    "PRIVILEGED_ROLES_REQUIRE_MFA", "True" if not DEBUG else "False"
).lower() in ["true", "1", "yes"]
PRIVILEGED_MFA_ROLE_NAMES = tuple(
    r.strip()
    for r in os.environ.get(
        "PRIVILEGED_MFA_ROLE_NAMES",
        "Super Admin,Company Admin,Payroll Admin,IT Admin",
    ).split(",")
    if r.strip()
)
# Celery Configuration Options
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_TIMEZONE = "UTC"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'tracker_screenshot': '120/min',
    'tracker_login': '10/min',
    'auth_login': '10/min',
    'auth_refresh': '30/min',
    'auth_mfa': '10/min',
    'auth_face': '10/min',
}
