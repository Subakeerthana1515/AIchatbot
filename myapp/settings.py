from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url


# 1. BASE_DIR: Confirm it's your project root (e.g., D:\django\myapp)
BASE_DIR = Path(__file__).resolve().parent.parent

## 2. Load the .env file from correct path
env_path = os.path.join(BASE_DIR, 'techjays', 'chatbot', '.env')
load_dotenv(dotenv_path=env_path)

# 3. Debug: Print values to confirm loading
print("ENV PATH:", env_path)
print("DATABASE_URL =", os.getenv("DATABASE_URL"))


SECRET_KEY = 'django-insecure-c65a2!yk($570)pwo1)g$v%m5m@ug0ls!$kx1&21y*pt7#cjhk'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'techjays',
    'techjays.chatbot',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Place corsheaders early
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'myapp.urls'  # Make sure your root urls.py is here

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # global templates folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myapp.wsgi.application'

# 4. Set up database from env
DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'techjays' / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/techjays/login_view/'



# Email backend for testing

DEFAULT_FROM_EMAIL = 'your_email@techjays.com'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'b89f4e450c8892'
EMAIL_HOST_PASSWORD = 'c5bca38df36b42'
EMAIL_USE_TLS = True

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
