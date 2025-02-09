from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django_htmx.http import trigger_client_event
from django.views.decorators.csrf import csrf_exempt

from .models import User_Profile, Notification
from strategies.models import Strategy
from automate.views import account_subscription_failed

from .forms import User_ProfileForm, PaymentCardForm, UserCreationEmailForm
from django_htmx.http import HttpResponseClientRedirect, retarget
from django.db.models import Max
from strategies.models import *

from django.core.mail import EmailMessage


from .tasks import *

import datetime
import environ
env = environ.Env()

from .utils.tradingview import *

import stripe
stripe.api_key = env('STRIPE_API_KEY')
stripe_wh_secret = env('STRIPE_API_WEBHOOK_SECRET')

from django.conf import settings
PRICE_LIST = settings.PRICE_LIST
PRICES = settings.PRICES

from allauth.account.signals import user_signed_up
from django.dispatch import receiver

@receiver(user_signed_up)
def send_welcome_email_allauth(request, user, **kwargs):
    print('new user sign up ... ', user.email)

@login_required(login_url='login')
def home(request):
    step = 1
    user_profile = False

    if request.has_subscription == None:
        step = 1
    else:
        if request.has_subscription == True and request.subscription_status != 'past_due':
            step = 2
        if request.user_profile:
            user_profile = request.user_profile
            
            if user_profile.tradingview_username:
                if 'step' in request.GET:
                    if request.GET.get('step') == '3':
                        step = 3
                
                else:
                    step = 4

    congrate = False
    if 'sub' in request.GET:
        if request.GET.get('sub') == 'True':
            congrate = True
            step = 2

    context = {"congrate": congrate, 'step':step , 'prices': settings.PRICES}

    if step == 4:
        res_num = 8
        new_strategies = Strategy.objects.filter(is_live=True).order_by('-created_at')[:res_num]
        most_viewed_strategies = Strategy.objects.filter(is_live=True).order_by('-view_count')[:res_num]
        new_results = StrategyResults.objects.all().order_by('-created_at')[:6]
        best_results = StrategyResults.objects.all().order_by('-created_at')[:6]
        new_ideas = StrategyComments.objects.all().order_by('-created_at')[:res_num]

        context['new_strategies'] = new_strategies
        context['most_viewed_strategies'] = most_viewed_strategies
        context['new_results'] = new_results
        context['best_results'] = best_results
        context['new_ideas'] = new_ideas

    return render(request,'home.html', context)

def membership(request):
    payment_form = PaymentCardForm()

    congrate = False
    if 'sub' in request.GET:
        if request.GET.get('sub') == 'True':
            congrate = True

    context = {"payment_form": payment_form, 'prices': settings.PRICES, "congrate": congrate}
    
    return render(request, 'membership.html', context)


@login_required(login_url='login')
def notifications_page(request):
    notifications = Notification.objects.filter(user=request.user_profile).order_by('-created_at')
    context = {'notifications': notifications}
    return render(request, 'notifications.html', context)

@login_required(login_url='login')
def settings_page(request):
    context = {}
    return render(request, 'settings.html', context)

@login_required(login_url='login')
def access_page(request):
    strategies = Strategy.objects.filter(is_live=True)
    context = {
        "strategies": strategies
    }
    return render(request, 'access.html', context)

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationEmailForm(request.POST) 
        # print(form)
        try:
            if form.is_valid():
                user = form.save(commit=False)
                user.email = user.username
                user.save()
                User_Profile.objects.create(user = user)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('home')
            else:
                messages.error(request, "An error occurred while registering")

        except Exception as e:
            print("An error occurred while registering", e)
            messages.error(request, "An error occurred while registering")

    return render(request,'auth/register.html', {'form': form})

def logout_user(request):
    logout(request)

    referer_url = request.META.get('HTTP_REFERER')
    return redirect(referer_url if referer_url else 'index')

def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username = email)
        except Exception as e:
            messages.error(request, "User does not exist!")
            return render(request, 'auth/login.html')

        user = authenticate(request, username = email, password = password)
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            return redirect('home')
        else:
            messages.error(request, "Email or Password incorrect!")

    return render(request, 'auth/login.html')

def get_profile(request):
    if request.user.is_authenticated:
        profile = User_Profile.objects.get(user=request.user)
        return render(request, 'profile.html', {'profile': profile})
    else:
        return render(request, 'profile.html')
    

@require_http_methods([ "POST"])
def update_user_password(request):
    if request.user.is_authenticated:
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return render(request, 'include/settings/password.html', {'msg': 'Password updated succesfully!'})

        # password = request.POST.get('password', '')
        # new_password = request.POST.get('new_password', '')
        # confirm_new_password = request.POST.get('confirm_new_password', '') 

        return render(request, 'include/settings/password.html', {'form': form})

@require_http_methods([ "POST"])
def edit_tradingview_username(request):

    page = request.GET.get('pg','')
    tv_username = request.POST.get('tradingview_username')


    if tv_username and request.user.is_authenticated:

        response_data = username_search(tv_username)
        if response_data == None:
            error = "an error occurred while searching for username. Please try again later."
            response = render(request, 'include/errors.html', context = {"error": error})
            return retarget(response, "#tradingview_username_submit_error")
        
        check_username = False
        for item in response_data:
            # print("ID:", item["username"])
            if item["username"] == tv_username:
                check_username = True

        if check_username == False:
            error = "The username provided cannot be found. Please ensure that you enter a valid TradingView username."
            response = render(request, 'include/errors.html', context = {"error": error})
            return retarget(response, "#tradingview_username_submit_error")
        
        is_tv_user_exist = User_Profile.objects.exclude(user=request.user).filter(tradingview_username=tv_username).exists()

        if is_tv_user_exist:
            error = "The username you entered has already been used by another account. If you believe this is a mistake, please contact us for further assistance."
            response = render(request, 'include/errors.html', context = {"error": error})
            return retarget(response, "#tradingview_username_submit_error")

        
        profile_user = request.user_profile

        profile_user.tradingview_username = tv_username

        profile_user.save()

        if request.has_subscription and request.subscription_status != 'past_due':
            strategies = Strategy.objects.all()

            for strategy in strategies:
                if strategy.is_live:
                    access_response = give_access(strategy.id, profile_user.id, True)

        # if access_response == None:
        #     error = "an error occurred while getting access. Please try again later or contact our support team."
        #     response = render(request, 'include/errors.html', context = {"error": error})
        #     return retarget(response, "#tradingview_username_submit_error")

        if not page:
            return HttpResponseClientRedirect(reverse('home') + '?step=3')
        else:
            response = render(request, 'include/settings/tradingview.html', {'succes': 'Username updated succesfully!'})
            return trigger_client_event(response, 'hide-animate')

    else:
        error = "Username is required."
        response = render(request, 'include/errors.html', context = {"error": error})
        return retarget(response, "#tradingview_username_submit_error")

@require_http_methods([ "POST"])
def get_access(request, strategy_id):
    pg = request.GET.get('pg')

    if request.user and request.has_subscription and request.subscription_status != 'past_due':
        profile_user = request.user_profile

        access_response = give_access(strategy_id, profile_user.id, True)

    if pg == "st":
        context = access_response
        response = render(request, 'include/get_access_model.html', context)
        return response
    else:
        strategies = Strategy.objects.filter(is_live=True)
        return render(request, 'include/access_list.html', context = {"strategies": strategies})
    

@require_http_methods([ "POST"])
def create_payment_method(request):
    if request.method == 'POST':
        data = request.POST
        
        context = {"error": '', 'payment_methods' : None}
        payment_method = data['pm_id']

        if not payment_method:
            context["error"] = 'No payment method has been detected.'
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-payment_methods")

        profile_user = User_Profile.objects.get(user=request.user)
        customer_id = profile_user.customer_id

        try:
            print("Adding payment method ...", payment_method, customer_id)
            stripe.PaymentMethod.attach(
                payment_method,
                customer=customer_id,
            )
            
            context["payment_methods"] = stripe.Customer.list_payment_methods(customer_id)

            response = render(request, 'include/payment_methods.html', context)
            return retarget(response, "#setting-payment_methods")
            # stripe.Customer.modify(
            #     customer_id,
            #     invoice_settings={
            #         'default_payment_method': payment_method
            #     }
            # )
        except Exception as e:
            context["error"] = 'Attached payment to customer '+str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-payment_methods")


@require_http_methods([ "POST"])
def delete_payment_method(request):
    if request.method == 'POST':
        data = request.POST
        
        context = {"error": '', 'payment_methods' : None}
        payment_method = data['pm_id']

        if not payment_method:
            context["error"] = 'No payment method has been detected.'

        profile_user = User_Profile.objects.get(user=request.user)
        customer_id = profile_user.customer_id

        try:
            subscriptions = stripe.Subscription.list(customer=customer_id, status="active")

            # Check if the payment method is used in any active subscription
            for subscription in subscriptions.auto_paging_iter():
                if subscription.default_payment_method == payment_method:
                    context["error"] = "This payment method is currently associated with an active subscription and cannot be deleted."
                    response = render(request, 'include/errors.html', context)
                    return retarget(response, "#stripe-error-delete-payment_methods")
            
            stripe.PaymentMethod.detach(payment_method)
            context["payment_methods"] = stripe.Customer.list_payment_methods(customer_id)

            response = render(request, 'include/payment_methods.html', context)
            return retarget(response, "#setting-payment_methods")
        
        except Exception as e:
            context["error"] = 'Attached payment to customer '+str(e)

            return retarget(response, "#stripe-error-delete-payment_methods")

@require_http_methods([ "POST"])
def setdefault_payment_method(request):
    if request.method == 'POST':
        data = request.POST
        
        context = {"error": '', 'payment_methods' : request.payment_methods }
        payment_method = data['pm_id']

        if not payment_method:
            context["error"] = 'No payment method has been detected.'

        profile_user = User_Profile.objects.get(user=request.user)
        customer_id = profile_user.customer_id

        try:
            customer = stripe.Customer.modify(
                    customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method
                    }
                )            
            context["stripe_customer"] = customer

            response = render(request, 'include/payment_methods.html', context)
            return retarget(response, "#setting-payment_methods")
        
        except Exception as e:
            context["error"] = 'Attached payment to customer '+str(e)

def check_coupon_fn(coupon_id, plan_id, price, customer_id):
    # print(coupon_id, plan_id, price)
    try:
        orig_price = price

        promotion_codes = stripe.PromotionCode.list(code=coupon_id, active=True)

        # Check if any promotion codes were returned
        if not promotion_codes.data:
            # print("No promotion codes found with the given code.")
            raise Exception("No promotion codes found with the given code.")
        else:
            # Use the first matching promotion code (if multiple, adjust logic as needed)
            promo_code = promotion_codes.data[0]
                # Step 2: Validate general properties
            is_active = promo_code.active
            expires_at = promo_code.expires_at
            max_redemptions = promo_code.max_redemptions
            times_redeemed = promo_code.times_redeemed
            restrictions = promo_code.restrictions

            # Validation logic for general properties
            if not is_active:
                raise Exception("Promotion code is inactive.")
            elif expires_at and expires_at < datetime.now().timestamp():
                raise Exception("Promotion code has expired.")
            elif max_redemptions and times_redeemed >= max_redemptions:
                raise Exception("Promotion code has reached its redemption limit.")

            # Step 3: Check customer-specific restrictions
            if restrictions.get("first_time_transaction", False):
                # If first-time transaction restriction is set, check if customer has transactions
                invoices = stripe.Invoice.list(customer=customer_id)
                if any(invoice.paid for invoice in invoices.auto_paging_iter()):
                    raise Exception("Promotion code is restricted to first-time transactions, and the customer is not eligible.")
                else:
                    print("Customer is eligible under first-time transaction restriction.")

            # Step 4: Check if the customer has already used the promotion code
            invoices = stripe.Invoice.list(customer=customer_id)
            has_used_promo_code = any(
                invoice.discount and invoice.discount.promotion_code == promo_code.id
                for invoice in invoices.auto_paging_iter()
            )

            if has_used_promo_code:
                raise Exception("Customer has already used this promotion code.")

            coupon = promo_code.coupon

        promo_id = promo_code.id

        if coupon.percent_off:
            price = round(price - (price * coupon.percent_off / 100), 2)

            coupon_off = str(-coupon.percent_off) + "%"
        elif coupon.amount_off:
            price = round(price - coupon.amount_off, 2)

            coupon_off = str(-coupon.amount_off) + '$'
        
        if coupon_id.find("QUAT") >= 0:
            if plan_id != "QUARTERLY":
                raise Exception("Coupon code is not valid for this plan.")
        elif coupon_id.find("MN") >= 0:
            if plan_id != "MONTHLY":
                raise Exception("Coupon code is not valid for this plan.")
        if plan_id == "LIFETIME":
            if coupon_id.find("BETA") >= 0:
                price = orig_price
                raise Exception("This is a beta plan, you cannot use it on lifetime plan.")
            
        return (price, coupon_off, promo_id)
    except Exception as e:
        # print(e)
        raise e

@require_http_methods([ "POST"])
def check_coupon(request):
    if request.method == 'POST':
        data = request.POST

        plan_id = request.GET.get('plan','')
        price_id = PRICE_LIST.get(plan_id, '')

        context = {"error": '', 'title': plan_id}
        context["coupon_val"] = ""

        if not price_id:
            context["error"] = 'No plan has been specified, please refresh the page and try again.'
            # return render(request, 'include/pay_form_stripe.html', context)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#"+context['title']+"-coupon-form-errors")

        orig_price = float(PRICES.get(plan_id, 0))  * 100
        price = orig_price
        
        coupon_id = data['coupon']

        if coupon_id:
            try:
                price, coupon_off, promo_id = check_coupon_fn(coupon_id, plan_id, price, request.user_profile.customer_id)

            except Exception as e:
                context["error"] = str(e)

                context["coupon_val"] = coupon_id
                context["base_price"] = str(orig_price / 100)
                context["final_price"] = str(orig_price / 100)

                response = render(request, 'include/pay_form_coupon.html', context)
                # response["hx-swap"] = "outerHTML" 
                return retarget(response, "#coupon-pay-"+context['title'])
                # response = render(request, 'include/errors.html', context)
                # return retarget(response, "#"+context['title']+"-coupon-form-errors")

            
            trial_days = 0
            trial_ends = datetime.datetime.now() + datetime.timedelta(days=trial_days)
            if trial_ends <= datetime.datetime.now() or plan_id == "LIFETIME":
                trial_ends = None
            
            context["staertime"] = trial_ends
            # context["price"] = txt_price
            # context["msg"] = str(trial_ends) +" Creating subscription " + txt_price

            context["succes"] = 'Coupon code is valid.'
            context["plan"] = plan_id  
            context["coupon_val"] = coupon_id
            context["coupon_off"] = coupon_off

            context["base_price"] = str(orig_price / 100)
            context["final_price"] = str(price / 100)

            # print(context)
            response = render(request, 'include/pay_form_coupon.html', context)
            # response["HX-Swap"] = "outerHTML" 
            return retarget(response, "#coupon-pay-"+context['title'])
        
        context["error"] = ''
        context["empty"] = True

        context["base_price"] = str(orig_price / 100)
        context["final_price"] = str(orig_price / 100)
        context["coupon_val"] = coupon_id
        
        response = render(request, 'include/pay_form_coupon.html', context)
        return retarget(response, "#coupon-pay-"+context['title'])

@require_http_methods([ "POST"])
def create_subscription_stripeform(request):
    if request.method == 'POST':
        data = request.POST

        plan_id = request.GET.get('plan','')
        price_id = PRICE_LIST.get(plan_id, '')

        context = {"error": '', 'title': plan_id}

        if not price_id:
            context["error"] = 'No plan has been specified, please refresh the page and try again.'
            # return render(request, 'include/pay_form_stripe.html', context)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])

        orig_price = float(PRICES.get(plan_id, 0))  * 100
        price = orig_price
        
        payment_method = data['pm_id']
        coupon_id = data['coupon']

        # trial_days = 3
        trial_days = 0
        if request.user_profile.subscription_id:
            trial_days = 0

        if coupon_id:
            try:
                price, price_off, promo_id = check_coupon_fn(coupon_id, plan_id, price, request.user_profile.customer_id)

            except Exception as e:
                context["error"] = 'Invalid coupon code '+str(e)
                response = render(request, 'include/errors.html', context)
                return retarget(response, "#stripe-error-"+context['title'])
        else:
            promo_id = None
            
        # if is_checking == "true":
        #     trial_ends = datetime.datetime.now() + datetime.timedelta(days=trial_days)
        #     if trial_ends <= datetime.datetime.now() or plan_id == "LIFETIME":
        #         trial_ends = None
        #     txt_price = str(price / 100)
        #     context["check"] = "false"
        #     context["staertime"] = trial_ends
        #     context["price"] = txt_price
        #     context["msg"] = str(trial_ends) +" Creating subscription " + txt_price
        #     response = render(request, 'include/pay_next.html', context)
        #     return retarget(response, "#stripe-next-"+context['title'])


        if not payment_method or payment_method == "None":
            context["error"] = 'No payment method has been detected.'
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])

        profile_user = request.user_profile
        customer_id = profile_user.customer_id

        try:
            stripe.PaymentMethod.attach(
                payment_method,
                customer=customer_id,
            )
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method
                }
            )
        except Exception as e:
            context["error"] = 'Attached payment to customer '+str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])
        try:
            old_subscription_id = profile_user.subscription_id

            if plan_id == "LIFETIME":

                lifetime = stripe.PaymentIntent.create(
                    amount=int(price),
                    currency="usd",
                    payment_method=payment_method,
                    confirm=True,
                    customer=customer_id,
                    description="Lifetime subscription.",
                    automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                    metadata={"price_id": price_id}
                )

                highest_lifetime_num = User_Profile.objects.aggregate(Max('lifetime_num'))['lifetime_num__max']
                lifetime_num = 1
                if highest_lifetime_num:
                    lifetime_num = lifetime_num + 1

                User_Profile.objects.filter(user = request.user).update(lifetime_intent=lifetime.id, is_lifetime=True, lifetime_num=lifetime_num)
                print("New lifetime has been created ...")
                
                send_new_lifetime_email_task(request.user.email)

                if len(old_subscription_id) > 0:
                    cancel_subscription = stripe.Subscription.delete(old_subscription_id)
                    print("Old subscription has been canceled ... ")

                    return HttpResponseClientRedirect(reverse('membership') + f'?sub=True')
                
                return HttpResponseClientRedirect(reverse('home') + f'?sub=True')
                
            
            metadata = {
                "profile_user_id": str(profile_user.id), 
            }

            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': price_id,
                }],
                payment_behavior="error_if_incomplete",
                default_payment_method=payment_method,
                # coupon=coupon_id,
                promotion_code=promo_id,
                trial_period_days=trial_days,
                trial_settings={"end_behavior": {"missing_payment_method": "pause"}},
                metadata=metadata,
            )

            User_Profile.objects.filter(user = request.user).update(subscription_id=subscription.id)
            print("New subscription has been created ...")

            if len(old_subscription_id) > 0:
                if request.subscription_status != 'canceled':
                    cancel_subscription = stripe.Subscription.delete(old_subscription_id)
                    print("Old subscription has been canceled ... ")

                return HttpResponseClientRedirect(reverse('membership') + f'?sub=True')
            else:
                send_new_member_email_task(request.user.email)

            # return JsonResponse(subscriptionId=subscription.id, clientSecret=subscription.latest_invoice.payment_intent.client_secret)
            return HttpResponseClientRedirect(reverse('home') + f'?sub=True')

        except Exception as e:
            context["error"] = "Creating subscription "  +str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])

@require_http_methods([ "POST"])
def update_subscription_stripeform(request):
    # TODO: check the payment form template and so when you close the form everything reset or when adding a coupon code change the button from subscribe to next
    if request.method == 'POST':
        data = request.POST

        plan_id = request.GET.get('plan','')
        
        price_id = PRICE_LIST.get(plan_id, '')

        context = {"error": '', 'title': plan_id}

        profile_user = request.user_profile
        customer_id = profile_user.customer_id

        old_subscription_id = profile_user.subscription_id
        old_subscription = request.subscription
        subscription_period_end = request.subscription_period_end
        subscription_status = request.subscription_status


        trial_ends = subscription_period_end
        if trial_ends <= datetime.datetime.now() or plan_id == "LIFETIME" or subscription_status == 'past_due':
            trial_ends = 'now'

        if not price_id:
            context["error"] = 'No plan has been specified, please refresh the page and try again.'
            # return render(request, 'include/pay_form_stripe.html', context)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])
        

        orig_price = float(PRICES.get(plan_id, 0))  * 100
        price = orig_price
        
        payment_method = data['pm_id']
        coupon_id = data['coupon']

        if coupon_id:
            try:
                price, price_off, promo_id = check_coupon_fn(coupon_id, plan_id, price, request.user_profile.customer_id)

            except Exception as e:
                context["error"] = 'Invalid coupon code '+str(e)
                response = render(request, 'include/errors.html', context)
                return retarget(response, "#stripe-error-"+context['title'])
        else:
            promo_id = None


        if not payment_method or payment_method == "None":
            context["error"] = 'No payment method has been detected.'
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])

        try:
            stripe.PaymentMethod.attach(
                payment_method,
                customer=customer_id,
            )
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method
                }
            )
        except Exception as e:
            context["error"] = 'Attached payment to customer '+str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])
        try:

            if plan_id == "LIFETIME":

                lifetime = stripe.PaymentIntent.create(
                    amount=int(price),
                    currency="usd",
                    payment_method=payment_method,
                    confirm=True,
                    customer=customer_id,
                    description="Lifetime subscription.",
                    automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                    metadata={"price_id": price_id}
                )

                highest_lifetime_num = User_Profile.objects.aggregate(Max('lifetime_num'))['lifetime_num__max']
                lifetime_num = 1
                if highest_lifetime_num:
                    lifetime_num = lifetime_num + 1

                User_Profile.objects.filter(user = request.user).update(lifetime_intent=lifetime.id, is_lifetime=True, lifetime_num=lifetime_num)
                print("New lifetime has been created ...")
                
                send_new_lifetime_email_task(request.user.email)

                if len(old_subscription_id) > 0:
                    cancel_subscription = stripe.Subscription.delete(old_subscription_id)
                    print("Old subscription has been canceled ... ")

                    return HttpResponseClientRedirect(reverse('membership') + f'?sub=True')
                
                return HttpResponseClientRedirect(reverse('home') + f'?sub=True')
                

            # subscription = stripe.Subscription.modify(
            #     old_subscription_id,
            #     cancel_at_period_end=False,
            #     # customer=customer_id,
            #     items=[{
            #         'id': old_subscription['items']['data'][0].id,
            #         'price': price_id,
            #     }],
            #     payment_behavior="error_if_incomplete",
            #     coupon=coupon_id,
            #     billing_cycle_anchor="now",
            #     proration_behavior='always_invoice',
            #     # trial_end=subscription_period_end,
            #     trial_end='now',
            # )

            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': price_id,
                }],
                payment_behavior="error_if_incomplete",
                # coupon=coupon_id,
                promotion_code=promo_id,
                trial_end=trial_ends,
                trial_settings={"end_behavior": {"missing_payment_method": "pause"}},
            )

            User_Profile.objects.filter(user = request.user).update(subscription_id=subscription.id)

            print("Subscription has been updated ...")

            cancel_subscription = stripe.Subscription.modify(old_subscription_id, cancel_at_period_end=True)
            print("Old Subscription has been canceled ...")


            # if len(old_subscription_id) > 0:
            #     if request.subscription_status != 'canceled':
            #         cancel_subscription = stripe.Subscription.delete(old_subscription_id)
            #         print("Old subscription has been canceled ... ")

            #     return HttpResponseClientRedirect(reverse('membership') + f'?sub=True')
            # else:
            #     send_new_member_email_task(request.user.email)

            # return JsonResponse(subscriptionId=subscription.id, clientSecret=subscription.latest_invoice.payment_intent.client_secret)
            return HttpResponseClientRedirect(reverse('membership') + f'?sub=True')

        except Exception as e:
            context["error"] = "Creating subscription "  +str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])

@require_http_methods([ "POST"])
def cancel_subscription(request):
    if request.method == 'POST':
        subscription = request.subscription
        subscription_period_end = request.subscription_period_end
        subscription_plan = request.subscription_plan
        subscription_status = request.subscription_status
        context = { 'subscription_status': subscription_status, 
                'subscription_period_end': subscription_period_end, 
                'subscription_plan':subscription_plan, 
                'subscription': subscription, 
                'error': "" } 

        if subscription.id:
            try:
                cancel_subscription = stripe.Subscription.modify(subscription.id, cancel_at_period_end=True)
                context['subscription'] = cancel_subscription
                context['subscription_status'] = cancel_subscription.status
                context['subscription_canceled'] = True

                end_timestamp = cancel_subscription.current_period_end * 1000
                end_time = datetime.datetime.fromtimestamp(end_timestamp / 1e3)
                context['subscription_period_end'] = end_time

                send_cancel_membership_email_task(request.user.email)

                return render(request, 'include/settings/membership.html', context)
            except Exception as e:
                pass

        context['error'] = 'An error occurred while attempting to cancel your subscription. Please contact us for assistance.'

        return render(request, 'include/settings/membership.html', context)


def preview_email(request):
    # Dummy data for template context
    context = {'user_name': 'Test User'}
    return render(request, 'emails/overdue_access_removed.html', context)

def send_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        content = request.POST.get('content')

        # if request.user.is_authenticated:
        #     email = request.user.username

        if not email:
            error = "Email address not provided!"
            response = render(request, 'include/errors.html', context = {"error": error})
            return retarget(response, "#contact_us_mail_error")

        if not subject:
            error = "Subject not provided!"
            response = render(request, 'include/errors.html', context = {"error": error})
            return retarget(response, "#contact_us_mail_error")

        if not content:
            error = "Message not provided!"
            response = render(request, 'include/errors.html', context = {"error": error})
            return retarget(response, "#contact_us_mail_error")

        if len(content) < 200:
            error = "Minimum message length is 200 characters!"
            response = render(request, 'include/errors.html', context={"error": error})
            return retarget(response, "#contact_us_mail_error")
        
        try:
            email_message = EmailMessage(
                subject,
                content,
                "noreply@isalgo.com",  # From email
                ['support@isalgo.com'],  # To email (your email)
                headers={'Reply-To': email}
            )

            files = request.FILES.getlist('documents')
            print("Number of files received:", len(files))
            # Attach document if present
            for file in files:
                # print(file.name)
                email_message.attach(file.name, file.read(), file.content_type)


            print('files get received')
            email_message.send()
            print('Email sent successfully!')

            response = render(request, 'include/docs/contact_us_form.html', context = {"succes": "Email sent successfully. We will get back to you in less than 48 hours."})

            return retarget(response, "#contact_us_mail")

        except Exception as e:
            print("Error sending maill", e)
            error = "An error occured please try again!"
            response = render(request, 'include/errors.html', context = {"error": error})
            return retarget(response, "#contact_us_mail_error")
        

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_wh_secret
        )

        subscription = event['data']['object']

        metadeta = event['data']['object']['metadata']

        if metadeta is not None and metadeta['broker_type'] is not None:
            if event['type'] == 'customer.subscription.deleted':
                account_subscription_failed(metadeta['broker_type'], subscription.id)
                
            elif event['type'] == 'customer.subscription.updated':
                print("Strip-Webhook: Subscription updated ...")

                if subscription.status == "canceld":
                    account_subscription_failed(metadeta['broker_type'], subscription.id)
                elif subscription.status == "past_due":
                    account_subscription_failed(metadeta['broker_type'], subscription.id)

            else:
                print('Unhandled event type {}'.format(event['type']))

        else:
            if event['type'] == 'customer.subscription.deleted':
                print("Strip-Webhook: Subscription deleted ...")

                remove_access(subscription.id)

            elif event['type'] == 'customer.subscription.updated':
                print("Strip-Webhook: Subscription updated ...")

                if subscription.status == "canceld":
                    remove_access(subscription.id)
                elif subscription.status == "past_due":
                    remove_access(subscription.id, False)

            else:
                print('Unhandled event type {}'.format(event['type']))

        return HttpResponse(status=200)

    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)


def remove_access(subscription_id, cancel_email = True):
    profile_user = User_Profile.objects.get(subscription_id=subscription_id)
    if profile_user:
        user = profile_user.user
            
        strategies = Strategy.objects.all()

        if profile_user.tradingview_username and profile_user.is_lifetime == False:
            for strategy in strategies:
                access_response = give_access(strategy.id, profile_user.id, False)
                
        if cancel_email:
            access_removed_email_task(user.email)

        # profile_user.deactivate_all_accounts()