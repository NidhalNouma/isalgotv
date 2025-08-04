from .base import *
import environ
env = environ.Env()
environ.Env.read_env()

# DEBUG = True
# DEBUG = False
ALLOWED_HOSTS = ["0.0.0.0", "127.0.0.1", "www.myproject.local", "myproject.local", "webhook.myproject.local", "taro.myproject.local"]

CORS_ALLOWED_ORIGINS = [
    "http://taro.myproject.local",
]

CSRF_TRUSTED_ORIGINS = ['http://*.myproject.local']

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME':  env('DATABASE_NAME'),
#         'USER':  env('DATABASE_USER'),
#         'PASSWORD':  env('DATABASE_PASS'),
#         'HOST':  env('DATABASE_HOST'),
#         'PORT': '5432',     
#     },
# }

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = 'us-east-1'

# Use Amazon S3 for static and media files
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Use Amazon S3 endpoint for your region
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'allauth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}