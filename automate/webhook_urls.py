from django.urls import path
from automate.views import *
from profile_user.views import stripe_webhook

urlpatterns = [
    path('c/<str:custom_id>', handle_webhook_crypto, name='webhook_crypto_request'),
    path('f/<str:custom_id>', handle_webhook_forex, name='webhook_forex_request'),

    path('whats-my-ip', get_server_ip, name='webhook_whats_my_ip'),
    path('stripe', stripe_webhook, name='webhook_handle_stripe'),
]


handler404 = webhook_404