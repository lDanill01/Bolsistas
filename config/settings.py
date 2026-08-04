import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

# Lê .env na raiz do projeto. Variáveis sensíveis podem vir via Docker Secrets
# usando _FILE (ex.: SECRET_KEY_FILE=/run/secrets/secret_key).
env.read_env(str(BASE_DIR / '.env'))


def read_secret(name):
    """Retorna valor de segredo: _FILE (Docker Secret) tem prioridade sobre env.
    Sempre faz strip() para evitar erros de whitespace no .env ou Docker Secrets."""
    file_key = f'{name}_FILE'
    file_path = env(file_key, default=None)
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    value = env(name, default=None)
    return value.strip() if value else value


SECRET_KEY = read_secret('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('SECRET_KEY deve estar definido no .env ou via Docker Secret.')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', 'bolsas.localhost'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # apps do projeto
    'base',
    'accounts',
    'cadastro',
    'editais',
    'classificacao',
    'notifications',
    'painel_bolsistas',

    # celery
    'django_celery_beat',
    'dj_celery_panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'base.middleware.LoginRequiredMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'base.context_processors.perfil_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': env('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
    }
}

# PostgreSQL: sobescreve quando as variáveis de conexão existem.
if env('DB_HOST', default=None):
    DATABASES['default'].update({
        'USER': env('DB_USER'),
        'PASSWORD': read_secret('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
    })

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Campo_Grande'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -----------------------------------------------------------------------------
# Storage de arquivos (media) — Azure Blob Storage em producao.
# Quando AZURE_ACCOUNT_NAME e AZURE_CONTAINER estao definidos, os arquivos
# enviados (curriculo, foto, anexos, documentos, documento de resultado) sao
# gravados em um container do Azure Blob. Caso contrario, usa o filesystem
# local (desenvolvimento).
# Credencial: se AZURE_CONNECTION_STRING ou AZURE_ACCOUNT_KEY forem fornecidos
# (via _FILE/secret), sao usados. Caso contrario, usa DefaultAzureCredential
# (managed identity do Container App) — recomendado. Nesse caso, conceda a role
# "Storage Blob Data Contributor" a identity do app no storage account.
# -----------------------------------------------------------------------------
AZURE_ACCOUNT_NAME = env('AZURE_ACCOUNT_NAME', default='')
AZURE_CONTAINER = env('AZURE_CONTAINER', default='')

if AZURE_ACCOUNT_NAME and AZURE_CONTAINER:
    STORAGES['default']['BACKEND'] = 'storages.backends.azure_storage.AzureStorage'
    AZURE_URL_EXPIRATION_SECS = env.int('AZURE_URL_EXPIRATION_SECS', default=300)
    _azure_connection_string = read_secret('AZURE_CONNECTION_STRING')
    _azure_account_key = read_secret('AZURE_ACCOUNT_KEY')
    if _azure_connection_string:
        AZURE_CONNECTION_STRING = _azure_connection_string
    elif _azure_account_key:
        AZURE_ACCOUNT_KEY = _azure_account_key

# Cache (Redis por padrao; locmem:// para dev local sem Docker)
CACHES = {
    'default': env.cache(default='redis://redis:6379/1'),
}

# Celery
if env('CELERY_BROKER_URL', default=None):
    CELERY_BROKER_URL = env('CELERY_BROKER_URL')
else:
    _rabbitmq_user = env('RABBITMQ_USER', default='bolsas')
    _rabbitmq_password = read_secret('RABBITMQ_PASSWORD')
    _rabbitmq_host = env('RABBITMQ_HOST', default='rabbitmq')
    _rabbitmq_vhost = env('RABBITMQ_VHOST', default='bolsas')
    if _rabbitmq_password:
        CELERY_BROKER_URL = (
            f'amqp://{_rabbitmq_user}:{_rabbitmq_password}@{_rabbitmq_host}:5672/{_rabbitmq_vhost}'
        )
    else:
        CELERY_BROKER_URL = f'amqp://{_rabbitmq_user}@{_rabbitmq_host}:5672/{_rabbitmq_vhost}'

CELERY_RESULT_BACKEND = env(
    'CELERY_RESULT_BACKEND',
    default='redis://redis:6379/0',
)
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 600  # 10 minutos
CELERY_RESULT_EXTENDED = True

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'fechar-editais-vencidos': {
        'task': 'editais.tasks.fechar_editais_vencidos',
        'schedule': crontab(hour=0, minute=5),
    },
}

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Email (recuperacao de senha e notificacoes).
# Em dev usamos o backend de console: o link de reset aparece nos logs do
# container `web` (docker compose logs web) — nao precisa de SMTP.
# Em producao, defina EMAIL_BACKEND=smtp via env + credenciais SMTP.
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = read_secret('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Bolsas SENAI-MS <no-reply@bolsas.localhost>')
EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX', default='[Bolsas SENAI-MS] ')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Seguranca em producao
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
    CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Traefik encaminha o protocolo original via X-Forwarded-Proto
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simples': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simples',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'painel_bolsistas': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'editais': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Integracao com IA (GROQ - Llama 3.3 70B)
# A GROQ expoe uma API compativel com o SDK openai, reaproveitado aqui via base_url.
GROQ_API_KEY = read_secret('GROQ_API_KEY')
GROQ_MODEL = env('GROQ_MODEL', default='llama-3.3-70b-versatile')
GROQ_BASE_URL = env('GROQ_BASE_URL', default='https://api.groq.com/openai/v1')

# Provedor de IA: 'groq' (unico suportado). Por padrao, ativa se a chave existir.
IA_PROVIDER = env('IA_PROVIDER', default='groq' if GROQ_API_KEY else '')

# Modo de execucao das tarefas de IA: True = Celery (async), False = sincrono
IA_ASYNC = env.bool('IA_ASYNC', default=True)

# Feriados nacionais para calculo de dias uteis (formato 'YYYY-MM-DD').
# Se vazia, feriados nao serao descontados dos dias uteis.
FERIADOS_NACIONAIS = []
