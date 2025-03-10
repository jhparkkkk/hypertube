"""
Django settings for hypertube project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-+%$-3g!4bxyrddh%i*phm@itbe!27dbpamvb@nd^p&yiwm!_&z'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

os.environ["DJANGO_SETTINGS_MODULE"] = "hypertube.settings"

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'oauth2_provider',
    'social_django', # omniauth for django
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'users',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),  
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000"
]
SESSION_COOKIE_SAMESITE = "Lax"

ROOT_URLCONF = 'hypertube.urls'

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

WSGI_APPLICATION = 'hypertube.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hypertube_db',
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': 'db',
        'PORT': '5432',
    }
}

AUTHENTICATION_BACKENDS = [
    'users.backends.FortyTwoOAuth2',              # custom backend 42
    'social_core.backends.github.GithubOAuth2',   # github
    'django.contrib.auth.backends.ModelBackend',  # email/pwd
]
AUTH_USER_MODEL = "users.User"

SOCIAL_AUTH_GITHUB_KEY = os.getenv("SOCIAL_AUTH_GITHUB_KEY")
SOCIAL_AUTH_GITHUB_SECRET = os.getenv("SOCIAL_AUTH_GITHUB_SECRET")
SOCIAL_AUTH_FORTYTWO_KEY = os.getenv("SOCIAL_AUTH_42_KEY")
SOCIAL_AUTH_FORTYTWO_SECRET = os.getenv("SOCIAL_AUTH_42_SECRET")
SOCIAL_AUTH_FORTYTWO_REDIRECT_URI = os.getenv("SOCIAL_AUTH_42_REDIRECT_URI")
SOCIAL_AUTH_URL_NAMESPACE = "social"

print("[DEBUG] SOCIAL_AUTH_GITHUB_KEY", SOCIAL_AUTH_GITHUB_KEY)
print("[DEBUG] SOCIAL_AUTH_GITHUB_SECRET", SOCIAL_AUTH_GITHUB_SECRET)
print("[DEBUG] SOCIAL_AUTH_42_KEY", SOCIAL_AUTH_FORTYTWO_KEY)
print("[DEBUG] SOCIAL_AUTH_42_SECRET", SOCIAL_AUTH_FORTYTWO_SECRET)

SOCIAL_AUTH_GITHUB_SCOPE = ["user:email",]

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'users.pipeline.associate_by_email',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'users.pipeline.set_auth_provider',
    'users.pipeline.set_profile_picture',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)
SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = ['provider', 'auth_provider']
LOGIN_REDIRECT_URL = "http://localhost:3000/" 
LOGOUT_REDIRECT_URL = "http://localhost:3000/"


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
