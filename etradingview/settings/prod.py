from .base import *
import environ
import mimetypes

mimetypes.add_type("text/html", ".html", True)
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("text/js", ".js", True)

env = environ.Env()
environ.Env.read_env()

DEBUG = False

ALLOWED_HOSTS = [
    '0.0.0.0',
    'isalgo.com',
    '*'
]

CSRF_TRUSTED_ORIGINS = ['https://*.isalgo.com','https://*.127.0.0.1','http://*.isalgo.com','http://*.127.0.0.1']

# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME':  env('DATABASE_NAME'),
#         'USER':  env('DATABASE_USER'),
#         'PASSWORD':  env('DATABASE_PASS'),
#         'HOST':  env('DATABASE_HOST'),
#         'PORT': '3306',
#         'OPTIONS': {
#             'sql_mode': 'traditional',
#         }
#     }
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