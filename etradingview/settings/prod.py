from .base import *
import environ

env = environ.Env()
environ.Env.read_env()

DEBUG = False

ALLOWED_HOSTS = [
    '127.0.0.1',
    'isalgo.com',
    'test.isalgo.com',
    'www.isalgo.com',
    '*'
]

CSRF_TRUSTED_ORIGINS = ['https://*.isalgo.com']

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':  env('DATABASE_NAME'),
        'USER':  env('DATABASE_USER'),
        'PASSWORD':  env('DATABASE_PASS'),
        'HOST':  env('DATABASE_HOST'),
        'PORT': 3306,
        'OPTIONS': {
            'sql_mode': 'traditional',
        }
    }
}

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = 'us-east-1'

AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
AWS_LOCATION = 'static'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Use Amazon S3 for static and media files
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

COMPRESS_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
COMPRESS_URL = STATIC_URL

COMPRESS_OFFLINE = True

# Logs for aws cloud watch
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',  # Adjust as needed
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',  # Adjust as needed
            'propagate': True,
        },
        'django-allauth': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

