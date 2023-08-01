from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':  env('DATABASE_NAME'),
        'USER':  env('DATABASE_USER'),
        'PASSWORD':  env('DATABASE_PASS'),
        'HOST':  env('DATABASE_HOST'),
        'PORT': '3306',
    }
}

# print(SECRET_KEY)