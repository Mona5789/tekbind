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
    'home'
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
  cloud_name = 'dgkkkzsw6', 
  api_key = '622381483739986', 
  api_secret = '7HMzVoxSYlTCIoS8cVASsruGeFI',
  secure = True
)
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
