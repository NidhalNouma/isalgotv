from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    '0.0.0.0',
    'isalgo.com',
    # '*'
]

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
