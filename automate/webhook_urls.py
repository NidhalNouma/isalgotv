from django.urls import path
from .views import *

urlpatterns = [
    path('c/<str:custom_id>', handle_webhook_crypto, name='webhook_crypto_request'),
    path('f/<str:custom_id>', handle_webhook_forex, name='webhook_forex_request'),
]