from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from .models import User_Profile
from .forms import User_ProfileForm, PaymentCardForm
from django_htmx.http import HttpResponseClientRedirect

import environ
env = environ.Env()

import stripe
stripe.api_key = env('STRIPE_API_KEY')

# Create your views here.

@login_required(login_url='login')
def home(request):
    step = 1

    if 'user_profile' in request:
        user_profile = request.user_profile
    else:
        user_profile = False

    congrate = False
    if 'sub' in request.GET:
        if request.GET.get('sub') == 'True':
            congrate = True
            step = 2
    
    request.GET = request.GET.copy()
    request.GET.clear()

    context = {'user_profile': user_profile, "congrate": congrate, 'step':step }
    return render(request,'home.html', context)

def membership(request):
    payment_form = PaymentCardForm()
    if 'user_profile' in request:
        user_profile = request.user_profile
    else:
        user_profile = False
    # print(request.user_profile)
    return render(request, 'membership.html', {'user_profile': user_profile, "payment_form": payment_form})

def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST) 
        # print(form)
        if form.is_valid():
            user = form.save(commit=False)
            print("user ", user)
            user.email = user.username
            user.save()
            User_Profile.objects.create(user = user)
            login(request, user)
            return redirect('home')
        else:
            print(form.errors)
            messages.error(request, "An error occurred while registering")

    return render(request,'auth/register.html', {'form': UserCreationForm()})

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
            user = User.object.get(username = email)
        except:
            messages.error(request, "User does not exist!")

        user = authenticate(request, username = email, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Email or Password does not exist!")

    
    return render(request, 'auth/login.html')

def get_profile(request):
    if request.user.is_authenticated:
        profile = User_Profile.objects.get(user=request.user)
        return render(request, 'profile.html', {'profile': profile})
    else:
        return render(request, 'profile.html')
    

@require_http_methods([ "POST"])
def edit_tradingview_username(request):
    if request.user.is_authenticated:
        profile_user = User_Profile.objects.get(user=request.user)

        profile_user.tradingview_username = request.POST.get('tradingview_username')
        profile_user.save()
        return HttpResponseClientRedirect(reverse('home') + f'?sub=True')



@require_http_methods([ "POST"])
def create_subscription(request):
    if request.method == 'POST':
        return HttpResponseClientRedirect(reverse('home') + f'?sub=True')

        plan_id = request.GET.get('plan','')
        if not plan_id:
            context = {"error": 'No plan has been specified, please refresh the page and try again.'}
            return render(request, 'include/pay_form.html', context)

        data = request.POST

        card_name = data['cardName']
        card_number = data['cardNumber'].replace(" ", "")
        card_exp_year = data['cardExpYear']
        card_exp_month = data['cardExpMonth']
        card_cvc = data['cardCVC']

        form = PaymentCardForm({
            'card_name': card_name ,
             'card_number': card_number, 
             'card_exp_year': card_exp_year, 
             'card_exp_month': card_exp_month, 
             'card_cvc': card_cvc
             })
        
        payment_method = None

        if form.is_valid():
            try:
                payment_method = stripe.PaymentMethod.create(
                    type="card",
                    card={
                        "number": card_number,
                        "exp_month": card_exp_month,
                        "exp_year": card_exp_year,
                        "cvc": card_cvc,
                    },
                )
            except Exception as e:
                context = {"error": str(e)}
                return render(request, 'include/pay_form.html', context)
        else:
            context = {"error": str(form.errors)}
            return render(request, 'include/pay_form.html', context)

        
        print(payment_method)
        profile_user = User_Profile.objects.get(user=request.user)
        customer_id = profile_user.customer_id
        price_id = 1 #data['priceId']

        try:
            stripe.PaymentMethod.attach(
                payment_method.id,
                customer=customer_id,
            )
        except Exception as e:
            context = {"error": str(e)}
            return render(request, 'include/pay_form.html', context)
        try:
            # Create the subscription. Note we're expanding the Subscription's
            # latest invoice and that invoice's payment_intent
            # so we can pass it to the front end to confirm the payment
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': price_id,
                }],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
            )

            User_Profile.objects.filter(user = request.user).update(subscription_id=subscription.id)
            return JsonResponse(subscriptionId=subscription.id, clientSecret=subscription.latest_invoice.payment_intent.client_secret)

        except Exception as e:
            context = {"error": str(e)}
            return render(request, 'include/pay_form.html', context)
