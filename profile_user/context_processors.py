# context_processors.py

from django.conf import settings
import json
from django.forms.models import model_to_dict
import environ
env = environ.Env()

def profile_context(request):

    user_profile = getattr(request, 'user_profile', None)

    server_ip =  getattr(request, 'server_ip', '') 
    if server_ip: server_ip = request.server_ip[0]

    return {
        'stripe_customer': getattr(request, 'stripe_customer', None),
        'user_profile': user_profile,
        'payment_methods': getattr(request, 'payment_methods', None),
        'prices': getattr(request, 'prices', None),

        'notifications': getattr(request, 'notifications', False),

        'server_ip': server_ip,

        "stripe_public_key": env('STRIPE_API_PUBLIC_KEY'),

        'IS_PRODUCTION': True if settings.DEBUG == False else False,
    }