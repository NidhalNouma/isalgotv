from .models import User_Profile, Notification
from django.urls import resolve, reverse

import re
import datetime
import time
import requests

import environ
env = environ.Env()

server_ip = env('WEBHOOK_SERVER_IP', None)

def get_stored_server_ip(request):
    global server_ip

    if server_ip:
        return server_ip

    server_ip_req = requests.get('https://ifconfig.me')
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
        subscription = None
        subscription_period_end = None
        subscription_active = None
        subscription_status = None
        subscription_price_id = None
        subscription_plan = None
        payment_methods = None
        stripe_customer = None
        has_subscription = False
        subscription_canceled = False

        total_amount_due = 0.0
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
            # print("user profile", user_profile.stripe_obj)

            request.user_profile = user_profile

            has_subscription = user_profile.has_subscription

            stripe_customer = user_profile.stripe_obj.get('customer', None)
            subscription = user_profile.stripe_obj.get('subscription', None)
            payment_methods = user_profile.stripe_obj.get('payment_methods', None)
            subscription_canceled = user_profile.stripe_obj.get('subscription_canceled', False)
            total_amount_due = user_profile.stripe_obj.get('subscription_next_payment_amount', 0.0)
            

            if user_profile.is_lifetime:
                has_subscription = True

            elif user_profile.subscription_id and user_profile.is_lifetime == False:

                subscription = user_profile.stripe_obj.get('subscription', None)

                if subscription:

                # Parse stored ISO string back to datetime if needed
                    sub_end = user_profile.stripe_obj.get('subscription_period_end', None)
                    if isinstance(sub_end, str):
                        try:
                            subscription_period_end = datetime.datetime.fromisoformat(sub_end)
                        except ValueError:
                            subscription_period_end = None
                    else:
                        subscription_period_end = sub_end


                    
                    subscription_active = user_profile.stripe_obj.get('subscription_active', None)
                    subscription_status =   user_profile.stripe_obj.get('subscription_status', None)
                    subscription_price_id = user_profile.stripe_obj.get('subscription_price_id', None)

                    subscription_plan = user_profile.stripe_obj.get('subscription_plan', None)



            # notifications = Notification.objects.filter(user=user_profile).order_by('-created_at')

        
        request.stripe_customer = stripe_customer
        request.user_profile = user_profile
        request.subscription = subscription
        request.payment_methods = payment_methods
        request.subscription_next_payment_amount = total_amount_due

        request.subscription_period_end = subscription_period_end
        request.subscription_active = subscription_active
        request.subscription_status = subscription_status
        request.subscription_price_id = subscription_price_id
        request.subscription_plan = subscription_plan
        # request.notifications = notifications

        # print("sub", subscription)

        request.has_subscription = has_subscription
        request.subscription_canceled = subscription_canceled

        request.server_ip = get_stored_server_ip(request),


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

        request.free_trial_days = env('FREE_TRIAL_DAYS')

        response = self.get_response(request)
        return response