from .models import User_Profile
import environ
env = environ.Env()

import stripe
stripe.api_key = env('STRIPE_API_KEY')
# print(stripe.api_key)

def check_user_and_stripe_middleware(get_response):
    # One-time configuration and initialization.

    def middleware(request):
        # print("stripe midl")
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        current_user = request.user

        if current_user.is_authenticated:
            try: 
                user_profile = User_Profile.objects.get(user=current_user)
            except User_Profile.DoesNotExist:
                user_profile = User_Profile.objects.create(user=current_user)

            if not user_profile.customer_id:
                customer = stripe.Customer.create(
                        email=current_user.email,
                        name=current_user.username,
                        # shipping={
                        #     "address": {
                        #     "city": "Brothers",
                        #     "country": "US",
                        #     "line1": "27 Fredrick Ave",
                        #     "postal_code": "97712",
                        #     "state": "CA",
                        #     },
                        #     "name": "{{CUSTOMER_NAME}}",
                        # },
                        # address={
                        #     "city": "Brothers",
                        #     "country": "US",
                        #     "line1": "27 Fredrick Ave",
                        #     "postal_code": "97712",
                        #     "state": "CA",
                        # },
                    )
                # print(customer)
                if customer.id:
                    user_profile = User_Profile.objects.filter(user=current_user).update(customer_id=customer.id)

            request.user_profile = user_profile
        
        response = get_response(request)


        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware