# monitoreo_proyecto/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# SEGURIDAD
# ============================================
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-clave-por-defecto-cambia-en-produccion')
DEBUG = os.environ.get('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

# ============================================
# BASE DE DATOS
# ============================================
# Detectar si estamos en Docker
DOCKER_ENV = os.environ.get('DOCKER_ENV', '0') == '1'

if DOCKER_ENV:
    # Configuración para Docker
    DB_HOST = 'db'
    REDIS_HOST = 'redis'
else:
    # Configuración para desarrollo local
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'monitoreo_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': DB_HOST,
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# ============================================
# CELERY / REDIS
# ============================================
REDIS_URL = os.environ.get('REDIS_URL', f'redis://{REDIS_HOST}:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Caracas'

# ============================================
# CELERY BEAT
# ============================================
CELERY_BEAT_SCHEDULE = {
    'network-monitor': {
        'task': 'monitoreo_app.tasks.run_network_monitor',
        'schedule': 10.0,
    },
    'http-monitor': {
        'task': 'monitoreo_app.tasks.run_http_monitor',
        'schedule': 30.0,
    },
}

# ============================================
# TELEGRAM (Fallback a variables de entorno)
# ============================================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

ALERT_SETTINGS = {
    'TELEGRAM_ENABLED': True,
    'NOTIFY_ON_DOWN': True,
    'NOTIFY_ON_RECOVERY': True,
    'NOTIFY_ON_WARN': True,
}

# ============================================
# APPS, MIDDLEWARE, TEMPLATES, ETC.
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'monitoreo_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'monitoreo_proyecto.urls'

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

WSGI_APPLICATION = 'monitoreo_proyecto.wsgi.application'

# ============================================
# INTERNACIONALIZACIÓN
# ============================================
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True

# ============================================
# ARCHIVOS ESTÁTICOS
# ============================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'monitoreo_app/static'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'