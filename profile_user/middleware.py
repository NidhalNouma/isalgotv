from .models import User_Profile, Notification
import environ
import datetime
import time
env = environ.Env()

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
        # notifications = None

        if current_user.is_authenticated:
            try: 
                user_profile = User_Profile.objects.get(user=current_user)
            except User_Profile.DoesNotExist:
                user_profile = User_Profile.objects.create(user=current_user)

            if user_profile.customer_id:
                try:
                    stripe_customer = stripe.Customer.retrieve(user_profile.customer_id)
                except Exception as e:
                    print("Error with getting stripe customer...", e)

            if not user_profile.customer_id or not stripe_customer:
                customer = stripe.Customer.create(
                        email=current_user.email,
                        name=current_user.username,
                    )
                # print(customer)
                if customer.id:
                    user_profile = User_Profile.objects.get(user=current_user)
                    user_profile.customer_id = customer.id
                    user_profile.save()

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
                    for key, val in PRICE_LIST.items():  
                        if val == subscription_price_id: 
                            subscription_plan = key

                    if subscription_status == 'active' and subscription.current_period_end > time.time():
                        has_subscription = True
                    elif subscription.status == "canceled" and subscription.current_period_end > time.time():
                        has_subscription = True
                    elif subscription.status == "incomplete":
                        has_subscription = False

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
        request.subscription_plan = subscription_plan
        request.payment_methods = payment_methods
        # request.notifications = notifications

        # print("sub", subscription)

        request.has_subscription = has_subscription

        
        response = get_response(request)

        # print(subscription)
        # print(subscription_period_end)
        # print(subscription_status)
        # print(subscription_active)
        # print(stripe_customer)


        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware