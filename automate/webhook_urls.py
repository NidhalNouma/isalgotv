from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from automate.views import *
from profile_user.views import stripe_webhook

urlpatterns = [
    path('whats-my-ip', get_server_ip, name='webhook_whats_my_ip'),
    path('stripe', stripe_webhook, name='webhook_handle_stripe'),
]

urlpatterns += i18n_patterns(
    path('c/<str:custom_id>', handle_webhook_crypto, name='webhook_crypto_request'),
    path('f/<str:custom_id>', handle_webhook_forex, name='webhook_forex_request'),

    path('i18n/', include('django.conf.urls.i18n')),
    prefix_default_language=False,
)


handler404 = webhook_404