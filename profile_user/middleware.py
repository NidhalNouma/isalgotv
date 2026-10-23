from profile_user.models import User_Profile, Notification
from profile_user.utils.stripe import subscription_object
from django.utils.translation import activate, get_language
from django.conf import settings as django_settings

import requests
from django.urls import reverse

import environ
env = environ.Env()

server_ip = env('WEBHOOK_SERVER_IP', None)

def get_stored_server_ip():
    global server_ip

    if server_ip:
        return server_ip

    server_ip_req = requests.get('https://ifconfig.me', timeout=5)
    server_ip = server_ip_req.text
    return server_ip


import stripe
stripe.api_key = env('STRIPE_API_KEY')

from django.conf import settings
PRICE_LIST = settings.PRICE_LIST

# TODO: Adding subscription stripe data to the session

def check_user_and_stripe_middleware(get_response):
    
    def middleware(request):

        current_user = request.user

        user_profile = None
        payment_methods = None
        stripe_customer = None
        
        # notifications = None

        if current_user.is_authenticated:
            try: 
                user_profile = User_Profile.objects.get(user=current_user)
            except User_Profile.DoesNotExist:
                user_profile = User_Profile.objects.create(user=current_user)


            user_profile.reset_token_usage_if_needed()

            get_updated_user_profile = False

            setup_intent = request.GET.get('setup_intent', None)
            if setup_intent:
                try:
                    setup_intent = stripe.SetupIntent.retrieve(setup_intent)
                    if setup_intent.status == 'succeeded':
                        get_updated_user_profile = True
                except stripe.error.StripeError as e:
                    setup_intent = None

            user_profile = user_profile.get_with_update_stripe_data(force=get_updated_user_profile)

            request.user_profile = user_profile

            # Restore saved language preference for authenticated users
            if user_profile.language:
                current_lang = get_language()
                if not current_lang or current_lang == django_settings.LANGUAGE_CODE:
                    activate(user_profile.language)


            stripe_customer = user_profile.stripe_obj.get('customer', None)
            payment_methods = user_profile.stripe_obj.get('payment_methods', None)

        request.stripe_customer = stripe_customer
        request.user_profile = user_profile

        request.payment_methods = payment_methods
        # request.notifications = notifications


        request.server_ip = get_stored_server_ip(),

        response = get_response(request)

        return response

    return middleware


from django.conf import settings
PRICE_LIST = settings.PRICE_LIST
PRICES = settings.PRICES

class MemberShipPricingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.prices = PRICES

        response = self.get_response(request)
        return response


import re
from django.shortcuts import redirect
from django.http import HttpResponse

# Paths reachable while the email is unverified (language prefix like /fr/ is stripped first)
_UNVERIFIED_ALLOWED = re.compile(r'^/(?:auth/(?:verify-email|verify-required|resend-verification|logout)|accounts/|static/|media/|i18n/)')
_LANG_PREFIX = re.compile(r'^/[a-z]{2}(?:[-_][A-Za-z]+)?(?=/)')

class EmailVerifiedMiddleware:
    """Blocks the site for logged-in users who haven't confirmed their email."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        profile = getattr(request, 'user_profile', None)

        if user.is_authenticated and profile and not profile.email_verified:
            path = request.path
            if not _UNVERIFIED_ALLOWED.match(path) and not _UNVERIFIED_ALLOWED.match(_LANG_PREFIX.sub('', path, count=1)):
                target = reverse('verify_required')
                if getattr(request, 'htmx', False):
                    response = HttpResponse(status=204)
                    response['HX-Redirect'] = target
                    return response
                return redirect(target)

        return self.get_response(request)
