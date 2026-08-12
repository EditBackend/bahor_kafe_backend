from pathlib import Path
import dj_database_url
import os


BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-k9df*mk5b0$5i1248-b!la7$4xdblvt)gyl3!(o@ttsq9#^3v1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['bahor-kafe-backend.onrender.com', '127.0.0.1', 'localhost']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'employee',
    'kitchen',
    'order',
    'table',
    'drf_yasg',
    'inventory',
    'sozlamalar',
    'users',
    'finance',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'storages',
]

# REST_FRAMEWORK = {
#     "DEFAULT_AUTHENTICATION_CLASSES": [
#         # "rest_framework.authentication.TokenAuthentication",
#     ],
#     "DEFAULT_PERMISSION_CLASSES": [
#         "rest_framework.permissions.IsAuthenticated",
#     ],
# }


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'employee.middleware.UpdateLastLoginMiddleware',
]

CORS_ALLOW_CREDENTIALS = True
ROOT_URLCONF = 'bahor_kafe_backend.urls'

CORS_ALLOW_ALL_ORIGINS = True

# TO'G'RILANDI: pastki chiziqlar o'rniga defis qo'yildi va frontend (localhost) manzillari qo'shildi
CORS_ALLOWED_ORIGINS = [
    "https://bahor-kafe-backend.onrender.com",
    "http://localhost:5173",  # Frontend local host manzili (image_a22345.jpg rasmida ko'ringan)
]

CSRF_TRUSTED_ORIGINS = [
    "https://bahor-kafe-backend.onrender.com",
]

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

WSGI_APPLICATION = 'bahor_kafe_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        # Agar tizimda DATABASE_URL bo'lsa uni oladi (Render'da),
        # bo'lmasa pastdagi Neon kodiga kompyuteringizdan ulanadi.
        default=os.environ.get(
            'DATABASE_URL',
            'postgresql://neondb_owner:npg_Wf15CBqPirtz@ep-polished-sun-apydg4h5-pooler.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
        )
    )
}

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

AUTH_USER_MODEL = 'employee.User'

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'uz'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True
USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
# Static fayllar URL va root
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_FILE_STORAGE = os.environ.get(
    'DEFAULT_FILE_STORAGE',
    'django.core.files.storage.FileSystemStorage'
)

if os.environ.get('AWS_STORAGE_BUCKET_NAME'):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None

STATICFILES_STORAGE = os.environ.get(
    'STATICFILES_STORAGE',
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
TELEGRAM_BOT_TOKEN = "8605510081:AAF2QRx4ihyCPYjJL3EUps-GX6ONaOY3KME"  # BotFather bergan token
# TELEGRAM_BOT_TOKEN = "8738213235:AAFsISWCvK27DpkXP8aOCKf56Uaj6yTZspI" # BotFather bergan token
TELEGRAM_CHAT_ID = "8235903420" # Xabar borishi kerak bo'lgan guruh yoki kanal ID si