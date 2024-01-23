from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django_htmx.http import trigger_client_event

from .models import User_Profile
from .forms import User_ProfileForm, PaymentCardForm
from django_htmx.http import HttpResponseClientRedirect, retarget

import datetime
import environ
env = environ.Env()

from .utils.tradingview import *

import stripe
stripe.api_key = env('STRIPE_API_KEY')

from django.conf import settings
PRICE_LIST = settings.PRICE_LIST

# Create your views here.

@login_required(login_url='login')
def home(request):
    step = 1
    user_profile = False

    if request.subscription == None:
        step = 1
    else:
        if request.subscription_active == True:
            step = 2
        if request.user_profile:
            user_profile = request.user_profile
            
            if user_profile.tradingview_username:
                step = 3
    
    # print('t ', request.subscription)
    # print('r ', request.subscription_period_end)
    # print('a ', request.subscription_active)
    # print('s ', request.subscription_status)
    # print('pid ', request.subscription_price_id)
    # print('pid ', request.subscription_plan)

    congrate = False
    if 'sub' in request.GET:
        if request.GET.get('sub') == 'True':
            congrate = True
            step = 2
    
    # request.GET = request.GET.copy()
    # request.GET.clear()

    context = {"congrate": congrate, 'step':step , 'prices': settings.PRICES}
    return render(request,'home.html', context)

def membership(request):
    payment_form = PaymentCardForm()

    context = {"payment_form": payment_form, 'prices': settings.PRICES}
    
    return render(request, 'membership.html', context)


@login_required(login_url='login')
def settings_page(request):
    context = {}
    return render(request, 'settings.html', context)

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST) 
        # print(form)
        if form.is_valid():
            user = form.save(commit=False)
            print("user ", user)
            user.email = user.username
            user.save()
            User_Profile.objects.create(user = user)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
        else:
            messages.error(request, "An error occurred while registering")

    return render(request,'auth/register.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('index')

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
                print('username exists ', tv_username)
                check_username = True

        if check_username == False:
            error = "Username not found. Please try again with another username."
            response = render(request, 'include/errors.html', context = {"error": error})
            return retarget(response, "#tradingview_username_submit_error")
        
        profile_user = User_Profile.objects.get(user=request.user)

        profile_user.tradingview_username = tv_username
        # TODO: give access to all available strategies
        access_response = give_access("0c8160c689014edfa61fc78efbbdbc59", tv_username, True)

        if access_response == None:
            error = "an error occurred while getting access. Please try again later or contact our support team."
            response = render(request, 'include/errors.html', context = {"error": error})
            return retarget(response, "#tradingview_username_submit_error")


        profile_user.save() 
        if not page:
            return HttpResponseClientRedirect(reverse('home'))
        else:
            response = render(request, 'include/settings/tradingview.html', {'user_profile': profile_user, 'msg': 'Username updated succesfully!'})
            return trigger_client_event(response, 'hide-animate')

    else:
        error = "Username is required."
        response = render(request, 'include/errors.html', context = {"error": error})
        return retarget(response, "#tradingview_username_submit_error")


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
            
            stripe.PaymentMethod.detach(payment_method)
            context["payment_methods"] = stripe.Customer.list_payment_methods(customer_id)

            response = render(request, 'include/payment_methods.html', context)
            return retarget(response, "#setting-payment_methods")
        
        except Exception as e:
            context["error"] = 'Attached payment to customer '+str(e)

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

@require_http_methods([ "POST"])
def create_subscription_stripeform(request):
    if request.method == 'POST':

        plan_id = request.GET.get('plan','')
        price_id = PRICE_LIST.get(plan_id, '')
        # csrf_token = request.POST.get('csrfmiddlewaretoken')

        context = {"error": '', 'title': plan_id}

        if not price_id:
            context["error"] = 'No plan has been specified, please refresh the page and try again.'
            # return render(request, 'include/pay_form_stripe.html', context)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])

        data = request.POST
        
        payment_method = data['pm_id']

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
                    amount=2680 * 100,
                    currency="usd",
                    payment_method=payment_method,
                    confirm=True,
                    customer=customer_id,
                    description="Lifetime subscription.",
                    automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                    metadata={"price_id": price_id}
                )

                User_Profile.objects.filter(user = request.user).update(lifetime_intent=lifetime.id, is_lifetime=True)
                print("New lifetime has been created ...")

                if len(old_subscription_id) > 0:
                    cancel_subscription = stripe.Subscription.delete(old_subscription_id)
                    print("Old subscription has been canceled ... ")

                    return HttpResponseClientRedirect(reverse('membership'))
                
                return HttpResponseClientRedirect(reverse('home') + f'?sub=True')
                

            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': price_id,
                }],
            )

            User_Profile.objects.filter(user = request.user).update(subscription_id=subscription.id)
            print("New subscription has been created ...")

            if len(old_subscription_id) > 0:
                cancel_subscription = stripe.Subscription.delete(old_subscription_id)
                print("Old subscription has been canceled ... ")

                return HttpResponseClientRedirect(reverse('membership') + f'?sub=True')

            # return JsonResponse(subscriptionId=subscription.id, clientSecret=subscription.latest_invoice.payment_intent.client_secret)
            return HttpResponseClientRedirect(reverse('home') + f'?sub=True')

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
                # cancel_subscription = stripe.Subscription.modify(subscription.id, cancel_at_period_end=True)
                cancel_subscription = stripe.Subscription.delete(subscription.id)
                context['subscription'] = cancel_subscription
                context['subscription_status'] = cancel_subscription.status

                end_timestamp = cancel_subscription.current_period_end * 1000
                end_time = datetime.datetime.fromtimestamp(end_timestamp / 1e3)
                context['subscription_period_end'] = end_time

                return render(request, 'include/settings/membership.html', context)
            except Exception as e:
                pass

        context['error'] = 'error occured while trying to cancel subscription.'

        return render(request, 'include/settings/membership.html', context)
    


