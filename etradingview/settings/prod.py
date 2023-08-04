from .base import *
import environ
# Initialise environment variables
env = environ.Env()
environ.Env.read_env()

# DEBUG = False

ALLOWED_HOSTS = [
    '0.0.0.0',
    'isalgo.com',
    '*'
]

CSRF_TRUSTED_ORIGINS = ['https://*.isalgo.com','https://*.127.0.0.1','http://*.isalgo.com','http://*.127.0.0.1']

# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':  env('DATABASE_NAME'),
        'USER':  env('DATABASE_USER'),
        'PASSWORD':  env('DATABASE_PASS'),
        'HOST':  env('DATABASE_HOST'),
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'traditional',
        }
    }
}