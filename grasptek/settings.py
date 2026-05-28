import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
if os.getenv("DJANGO_DEVELOPMENT") == "True":
    from dotenv import load_dotenv
    load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', "fallback-secret")
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin]
DEBUG = True
SESSION_COOKIE_AGE = 500 * 60
SESSION_EXPIRE_SECONDS = 75000
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1").split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'home',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'grasptek.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/')],
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

import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
    cloud_name='dgkkkzsw6',
    api_key='622381483739986',
    api_secret='7HMzVoxSYlTCIoS8cVASsruGeFI',
    secure=True
)
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
WSGI_APPLICATION = 'grasptek.wsgi.application'
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'HOST': os.getenv('HOST'),
#         'PORT': os.getenv('PORT'),
#         'NAME': os.getenv('NAME'),
#         'USER': os.getenv('USER'),
#         'PASSWORD': os.getenv('PASSWORD'),
#         'CONN_MAX_AGE': 600
#     }
# }

CSRF_TRUSTED_ORIGINS = [
    "https://tekbind.com",
    "https://www.tekbind.com",
    "https://secure.ccavenue.com",
    "https://test.ccavenue.com",
]

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://grasptek_user:Z9OeoUPOpZ402RBHScM9EoTfRSDeO9LX@dpg-d0ndun6mcj7s73dt26i0-a.oregon-postgres.render.com/grasptek',
        conn_max_age=600,
        ssl_require=False 
    )
}
# DATABASES = {
#      'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'HOST': "localhost",
#         'PORT': "5432",
#         'NAME': "grasptek",
#         'USER': "postgres",
#         'PASSWORD': "zxcvbnm@890",
#         'CONN_MAX_AGE': 600
#     }
# }
LOGIN_REDIRECT_URL = '/profile/'
STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, "static")

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static"), ]
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "tekbind7@gmail.com"
EMAIL_HOST_PASSWORD = 'oqtx bttp haua uzjs'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'

# ✅ Keep user logged in even after browser close
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ✅ Keep session for long time (1 year)
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365  

# ✅ Refresh session on every request (important)
SESSION_SAVE_EVERY_REQUEST = True

SESSION_COOKIE_SECURE = True      # Only if using HTTPS
SESSION_COOKIE_HTTPONLY = True
# ✅ Add BELOW this (separate setting)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),   # short-lived
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # long-lived
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
