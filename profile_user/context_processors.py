# context_processors.py

from django.conf import settings
import json
from django.forms.models import model_to_dict
import environ
env = environ.Env()

def profile_context(request):
    coupon = {
        "code": env('COUPON_CODE'),
        "off": env('COUPON_OFF'),
    }

    user_profile = getattr(request, 'user_profile', None)

    server_ip =  getattr(request, 'server_ip', '') 
    if server_ip: server_ip = request.server_ip[0]

    return {
        'stripe_customer': getattr(request, 'stripe_customer', None),
        'user_profile': user_profile,
        'subscription': getattr(request, 'subscription', None),

        'subscription_period_end': getattr(request, 'subscription_period_end', None),
        'subscription_active': getattr(request, 'subscription_active', None),
        'subscription_status': getattr(request, 'subscription_status', None),
        'subscription_next_payment_amount': getattr(request, 'subscription_next_payment_amount', None),

        'subscription_price_id': getattr(request, 'subscription_price_id', None),
        'subscription_plan': getattr(request, 'subscription_plan', None),
        'payment_methods': getattr(request, 'payment_methods', None),

        'has_subscription': getattr(request, 'has_subscription', False),
        'subscription_canceled': getattr(request, 'subscription_canceled', False),

        'prices': getattr(request, 'prices', None),
        'free_trial_days': getattr(request, 'free_trial_days', None),

        'notifications': getattr(request, 'notifications', False),
        'coupon': coupon,

        'server_ip': server_ip,

        'db_key':  env('FIREBASE_KEY'),

        "stripe_public_key": env('STRIPE_API_PUBLIC_KEY'),

        'IS_PRODUCTION': True if settings.DEBUG == False else False,
    }