from .models import User_Profile, Notification
import re
import datetime
import time
import requests

import environ
env = environ.Env()

server_ip_req = requests.get('https://ifconfig.me')
server_ip = server_ip_req.text
print("Webhook server IP address: " + server_ip)


import stripe
stripe.api_key = env('STRIPE_API_KEY')

from django.conf import settings
PRICE_LIST = settings.PRICE_LIST

# TODO: Adding subscription stripe data to the session

def check_user_and_stripe_middleware(get_response):
    # One-time configuration and initialization.
    
    def middleware(request):
        # print("stripe midl")
        # Code to be executed for each request before
        # the view (and later middleware) are called.

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

            if user_profile.customer_id:
                try:
                    stripe_customer = stripe.Customer.retrieve(user_profile.customer_id)
                    # print("stripe customer, " , stripe_customer)
                except Exception as e:
                    print("Error with getting stripe customer...", e)

            if not user_profile.customer_id or not stripe_customer or "deleted" in stripe_customer:
                customer = stripe.Customer.create(
                        email=current_user.email,
                        name=current_user.username,
                    )
                # print(customer)
                if customer.id:
                    # user_profile = User_Profile.objects.get(user=current_user)
                    user_profile.customer_id = customer.id
                    user_profile.save()
            
            # print("stripe customer, " , user_profile.customer_id)

            user_profile.reset_token_usage_if_needed()

            request.user_profile = user_profile

            if user_profile.is_lifetime:
                has_subscription = True

            elif user_profile.subscription_id and user_profile.is_lifetime == False:
                try:
                    subscription = stripe.Subscription.retrieve(user_profile.subscription_id)

                    end_timestamp = subscription.current_period_end * 1000
                    end_time = datetime.datetime.fromtimestamp(end_timestamp / 1e3)
                    subscription_period_end = end_time
                    subscription_active = subscription.plan.active
                    subscription_status = subscription.status
                    subscription_price_id = subscription.plan.id

                    subscription_product_id = subscription.plan.product
                    subscription_interval = subscription.plan.interval
                    subscription_interval_count = subscription.plan.interval_count

                    if subscription_interval == "year":
                        subscription_plan = list(PRICE_LIST.keys())[2]

                    elif subscription_interval == "month":
                        if subscription_interval_count == 1:
                            subscription_plan = list(PRICE_LIST.keys())[0]
                        elif subscription_interval_count == 3:
                            subscription_plan = list(PRICE_LIST.keys())[1]
                        elif subscription_interval_count == 12:
                            subscription_plan = list(PRICE_LIST.keys())[2]


                    # readable_date = datetime.datetime.fromtimestamp(next_payment_date).strftime('%Y-%m-%d %H:%M:%S')

                    # print(next_payment_date, total_amount_due, readable_date)

                    # for key, val in PRICE_LIST.items():  
                    #     if val == subscription_price_id: 
                    #         subscription_plan = key

                    # subscription_status = 'past_due'

                    if subscription_status == 'active' and subscription.current_period_end > time.time():
                        has_subscription = True
                    elif subscription_status == 'trialing' and subscription.current_period_end > time.time():
                        has_subscription = True
                    elif subscription_status == 'past_due' and subscription.current_period_end > time.time():
                        has_subscription = True
                    # elif subscription.status == "canceled" and subscription.current_period_end > time.time():
                    #     has_subscription = True
                    elif subscription.status == "incomplete":
                        has_subscription = False

                    if subscription.cancel_at_period_end or subscription.status == "canceled" or subscription.status == "incomplete":
                        subscription_canceled = True


                    if not subscription_canceled and has_subscription:
                        # Get the upcoming invoice for the subscription
                        upcoming_invoice = stripe.Invoice.upcoming(subscription=subscription)

                        # Extract the next payment details
                        # next_payment_date = upcoming_invoice["next_payment_attempt"]
                        if upcoming_invoice:
                            total_amount_due = upcoming_invoice["amount_due"]/100

                    # print(subscription_status, has_subscription)
                except Exception as e:
                    print("Error with getting stripe data ...", e)


            if user_profile.customer_id:
                try:
                    payment_methods = stripe.Customer.list_payment_methods(user_profile.customer_id, limit=100)
                    payment_methods = payment_methods.data
                except Exception as e:
                    print("Error with getting payment methods ...", e)

            # notifications = Notification.objects.filter(user=user_profile).order_by('-created_at')

        
        request.stripe_customer = stripe_customer
        request.user_profile = user_profile
        request.subscription = subscription
        request.subscription_period_end = subscription_period_end
        request.subscription_active = subscription_active
        request.subscription_status = subscription_status
        request.subscription_price_id = subscription_price_id
        request.subscription_next_payment_amount = total_amount_due
        request.subscription_plan = subscription_plan
        request.payment_methods = payment_methods
        # request.notifications = notifications

        # print("sub", subscription)

        request.has_subscription = has_subscription
        request.subscription_canceled = subscription_canceled

        request.server_ip = server_ip,

        response = get_response(request)

        # print(subscription)
        # print(has_subscription)
        # print(subscription_period_end)
        # print(subscription_status)
        # print(subscription_active)
        # print(stripe_customer)

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