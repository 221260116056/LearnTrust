"""
Django settings for learntrust project.
Student Panel Only – LearnTrust
"""

from pathlib import Path

# -------------------------------------------------
# BASE DIRECTORY
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------------------------
# SECURITY
# -------------------------------------------------
SECRET_KEY = 'django-insecure-change-this-in-production'

DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
]


# -------------------------------------------------
# APPLICATIONS (STUDENT PANEL ONLY)
# -------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Student panel apps
    'student',
    'payments',
    'streaming',
    'events',
    'quizzes',
    'certificates',
    'rest_framework',
]


# -------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# -------------------------------------------------
# URL CONFIG
# -------------------------------------------------
ROOT_URLCONF = 'learntrust.urls'


# -------------------------------------------------
# TEMPLATES
# -------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # REQUIRED
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


# -------------------------------------------------
# WSGI
# -------------------------------------------------
WSGI_APPLICATION = 'learntrust.wsgi.application'


# -------------------------------------------------
# DATABASE (PostgreSQL)
# -------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'learntrust_db',
        'USER': 'postgres',
        'PASSWORD': '12345678',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# -------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------
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


# -------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True


# -------------------------------------------------
# STATIC FILES
# -------------------------------------------------
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


# -------------------------------------------------
# MEDIA FILES
# -------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# -------------------------------------------------
# AUTHENTICATION (EMAIL LOGIN ENABLED)
# -------------------------------------------------
AUTHENTICATION_BACKENDS = [
    'student.authentication.EmailBackend',          # email login
    'django.contrib.auth.backends.ModelBackend',    # default
]

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'


# -------------------------------------------------
# DEFAULT PRIMARY KEY
# -------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


SECURE_SSL_REDIRECT = False   # keep False locally
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
