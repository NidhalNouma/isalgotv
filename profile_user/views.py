from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django_htmx.http import trigger_client_event
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
from django.core.cache import cache

from profile_user.models import User_Profile, Notification
from strategies.models import Strategy, StrategySubscriber

from profile_user.forms import User_ProfileForm, PaymentCardForm
from django_htmx.http import HttpResponseClientRedirect, retarget
from strategies.models import *

from django.core.mail import EmailMessage
from profile_user.utils.stripe import *
from profile_user.utils.tradingview import *
from profile_user.utils.discord import get_discord_user_id, add_role_to_user, remove_role_from_user
from profile_user.tasks import send_new_member_email_task, send_new_lifetime_email_task, send_cancel_membership_email_task

import random
import datetime
import json
import environ
env = environ.Env()


from django.conf import settings
PRICE_LIST = settings.PRICE_LIST
PRICES = settings.PRICES


# Array of helper questions for home view
QUESTIONS = [
    "Do you know that I can help you understand various trading strategies available on Isalgo?",
    "Do you know that I can guide you through the process of setting up your Isalgo account?",
    "Do you know that I can assist you in customizing trading strategies to fit your trading style?",
    "Do you know that I can show you how to install Isalgo strategies in TradingView?",
    "Do you know that I can explain how to take advantage of backtesting features to evaluate your strategies?",
    "Do you know that I can walk you through automating your trading with TradingView alerts?",
    "Do you know that I can help you set up alerts for your strategies to manage trades proactively?",
    "Do you know that I can provide you with detailed explanations of technical indicators used in trading strategies?",
    "Do you know that I can assist you in generating detailed trading reports based on your performance?",
    "Do you know that I can analyze specific trading charts and assets to identify market trends?",
    "Do you know that I can offer trading suggestions based on analytical data and insights?",
    "Do you know that I can provide advanced coding examples in Pine Script v6 for TradingView?",
    "Do you know that I can help you understand risk management techniques within your trading strategies?",
    "Do you know that I can show you how to use the built-in learning algorithm to enhance your trading decisions?",
    "Do you know that I can explain the different stop-loss methods available in Isalgo strategies?",
    "Do you know that I can help you review your trading performance and suggest improvements?",
    "Do you know that I can demonstrate how to access historical data for backtesting your strategies?",
    "Do you know that I can provide real-time updates on performance metrics for ongoing trades?",
    "Do you know that I can help you link your trading accounts to automate your trades?",
    "Do you know that I can guide you through the process of sharing your trading results with the Isalgo community?",
    "Do you know that I can provide insights into the best trading days and times based on historical performance?",
    "Do you know that I can explain how to effectively use trendlines and channels in your trading strategies?",
    "Do you know that I can support you with troubleshooting any issues you may encounter with Isalgo?",
    "Do you know that I can help you configure your trading sessions to optimize trade execution?",
    "Do you know that I can clarify how to utilize dynamic alerts for specific market events?",
    "Do you know that I can guide you on the significance of position sizing in your trading strategy?",
    "Do you know that I can help you evaluate which trading strategy might suit your risk tolerance better?",
    "Do you know that I can provide summaries of the top-performing strategies and their results on Isalgo?",
    "Do you know that I can assist you in understanding the setting adjustments for optimal strategy performance?",
    "Do you know that I can answer any specific questions you have about using Isalgo tools and features?"
]

quick_chart_symbols = [
    'ICMARKETS:XAUUSD',
    'ICMARKETS:EURUSD',
    'ICMARKETS:USDJPY',
    'ICMARKETS:GBPJPY',
    'ICMARKETS:GBPUSD',
    'ICMARKETS:USDCHF',
    'ICMARKETS:USDCAD',
    'ICMARKETS:AUDUSD',
    'BINANCE:BTCUSDT',
    'BINANCE:ADAUSDT',
    'OKX:ETHUSDT',
    'BINANCE:BNBUSDT',
    'BINANCE:XRPUSDT',
    'BITGET:LTCUSDT',
    'BYBIT:SOLUSDT',
    'BINANCE:DOGEUSDT',
    'KUCOIN:DOTUSDT',
    'COINBASE:AVAXUSD',
    'BINANCE:SHIBUSDT',
    'KUCOIN:VETUSDT',
    'KUCOIN:AXSUSDT',
    'KUCOIN:THETAUSDT',
    'BITMART:NEARUSDT',
    'BITMART:MANAUSDT',
    'BITMART:SANDUSDT',
    'BITMART:CHZUSDT',
]

def market_news():
    """
    Fetch recent 10 news articles related to forex, stock, and crypto markets.
    """
    try:
        NEWS_API_KEY = env('NEWS_API_KEY')
        if not NEWS_API_KEY:
            return JsonResponse({"error": "Missing NEWS_API_KEY in settings."}, status=500)

        url = "https://newsapi.org/v2/everything"
        query = "TradingView Or trading strategies OR forex trading strategies OR crypto trading strategies OR stock trading strategies"

        params = {
            "q": query,
            "language": "en",
            "pageSize": 30,
            "sortBy": "publishedAt",
            "apiKey": NEWS_API_KEY,
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") != "ok":
            return []

        articles = data.get("articles", [])
        r_articales = []
        for article in articles:
            if article.get("url") and article.get("title") and article.get("description") and article.get("urlToImage"):

                published_at = article.get("publishedAt")
                if published_at:
                    try:
                        # Convert ISO 8601 string (with trailing Z) to a datetime object
                        published_at = datetime.datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        published_at = None
                else:
                    published_at = None

                r_articales.append({
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "urlToImage": article.get("urlToImage"),
                    "publishedAt": published_at,
                    "source": article.get("source", {}).get("name"),
                })

        return r_articales
    except requests.RequestException as e:
        return []

def random_strategies_results_context():
    cash_timeout = 3600 * 6
    context = {}

    strategy_filter = {
        'is_live': True,
        'premium__in': ['Free', 'Elite', 'Premium'],
    }

    result_strategy_filter = {
        'strategy__is_live': True,
        'strategy__premium__in': ['Free', 'Elite', 'Premium'],
    }

    # Cache key names for each query
    new_strategies = cache.get('new_strategies')
    if new_strategies is None:
        new_strategies = list(Strategy.objects.filter(**strategy_filter).order_by('-created_at')[:8])
        cache.set('new_strategies', new_strategies, timeout=cash_timeout)
        
    random.shuffle(new_strategies)
    context['new_strategies'] = new_strategies[:6]

    most_viewed_strategies = cache.get('most_viewed_strategies')
    if most_viewed_strategies is None:
        most_viewed_strategies = list(
            Strategy.objects.filter(**strategy_filter).annotate(like_count=Count('likes')).order_by('-like_count')[:8]
        )
        cache.set('most_viewed_strategies', most_viewed_strategies, timeout=cash_timeout)

    random.shuffle(most_viewed_strategies)
    context['most_viewed_strategies'] = most_viewed_strategies[:6]

    best_results = cache.get('best_results')
    if best_results is None:
        best_results = list(
            StrategyResults.objects.filter(**result_strategy_filter).annotate(
                positive_votes_count=Count('positive_votes')
            ).order_by('-positive_votes_count')[:8]
        )
        cache.set('best_results', best_results, timeout=cash_timeout)

    random.shuffle(best_results)
    context['best_results'] = best_results[:6]

    new_results = cache.get('new_results')
    if new_results is None:
        new_results = list(StrategyResults.objects.filter(**result_strategy_filter).order_by('-created_at')[:8])
        cache.set('new_results', new_results, timeout=cash_timeout)

    random.shuffle(new_results)
    context['new_results'] = new_results[:6]

    comments = cache.get('comments')
    if comments is None:
        comments = list(StrategyComments.objects.filter(**result_strategy_filter).order_by('-created_at')[:6])
        cache.set('comments', comments, timeout=cash_timeout)

    random.shuffle(comments)
    context['comments'] = comments


    recent_news = cache.get('recent_news')
    if recent_news is None:
        recent_news = market_news()
        cache.set('recent_news', recent_news, timeout=cash_timeout)
    recent_news = market_news()

    context['recent_news'] = recent_news
    context['quick_chart_symbols'] = random.sample(quick_chart_symbols, 6)
    return context


@login_required(login_url='index')
def home(request):
    context = {}

    # Select a random helper question for the template
    # random_question = random.choice(QUESTIONS)
    # context['random_ai_question'] = random_question

    context = {**context, **random_strategies_results_context()}

    return render(request, 'home.html', context)

def membership(request):
    payment_form = PaymentCardForm()

    congrate = False
    if 'sub' in request.GET:
        if request.GET.get('sub') == 'True':
            congrate = True

    context = {"payment_form": payment_form, "congrate": congrate}
    
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
    strategy_filter = {
        'is_live': True,
        # 'premium__in': ['Free', 'Elite', 'Premium'],
    }

    strategies = Strategy.objects.filter(**strategy_filter)
    context = {
        "strategies": strategies,
        "free_strategies": strategies.filter(premium='Free'),
        "premium_strategies": strategies.filter(premium='Premium'),
        "elite_strategies": strategies.filter(premium='Elite'),
        "vip_strategies": strategies.filter(premium='VIP'),
    }
    return render(request, 'access.html', context)

def get_profile(request):
    if request.user.is_authenticated:
        profile = User_Profile.objects.get(user=request.user)
        return render(request, 'profile.html', {'profile': profile})
    else:
        return render(request, 'profile.html')
    

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
        profile_user.remove_access(include_free_strategies=True, remove_discord_role=False)
        profile_user.tradingview_username = tv_username
        profile_user.save()

        access_filter = {
            'is_live': True,
            'premium__in': ['Free'],
        }
        if request.has_subscription:
            access_filter = {
                'is_live': True,
                'premium__in': ['Free', 'Premium'],
            }
        if profile_user.is_lifetime:
            access_filter = {
                'is_live': True,
                'premium__in': ['Free', 'Elite', 'Premium'],
            }
        strategies = Strategy.objects.filter(**access_filter)

        for strategy in strategies:
            if strategy.is_live:
                access_response = profile_user.give_tradingview_access(strategy.id, access=True)
                if access_response.get('error'):

                    error = access_response.get('error')
                    response = render(request, 'include/errors.html', context = {"error": error})
                    return retarget(response, "#tradingview_username_submit_error")

        if not page:
            context = {}
            context["step"] = 3

            response = render(request, 'include/home_get_started.html', context)
            return retarget(response, "#home-get-started")
            # return HttpResponseClientRedirect(reverse('home') + '?step=3')
        elif page == "access":
            strategies = Strategy.objects.filter(is_live=True)
            context = {
                "strategies": strategies,
            }

            response = render(request, 'include/access_list.html', context)
            return response

        else:
            response = render(request, 'include/settings/tradingview.html', {'succes': 'Username updated succesfully!'})
            return trigger_client_event(response, 'hide-animate')

    else:
        error = "Username is required."
        response = render(request, 'include/errors.html', context = {"error": error})
        return retarget(response, "#tradingview_username_submit_error")

@require_http_methods([ "POST"])
def edit_discord_username(request):
    try:
        discord_username = request.POST.get('discord_username')

        if discord_username and request.user.is_authenticated:

            discord_user_id = get_discord_user_id(discord_username)
            if not discord_user_id:
                raise Exception("User not found on Discord")
                
            profile_user = request.user_profile
            if profile_user.discord_username:
                remove_role_from_user(profile_user.discord_username, profile_user.is_lifetime)

            if add_role_to_user(discord_user_id, profile_user.is_lifetime):
                profile_user.discord_username = discord_username
                profile_user.save()

                response = render(request, 'include/settings/discord.html', {'succes': 'User granted access!'})
                return trigger_client_event(response, 'hide-animate')
            else:
                raise Exception("Failed to add role.")

        else:
            raise Exception("Username is required.")
    
    except Exception as e:
        response = render(request, 'include/errors.html', context = {"error": e})
        return retarget(response, "#discord-form-errors")

@require_http_methods([ "POST"])
def get_access(request, strategy_id):
    try:
        pg = request.GET.get('pg')
        premium = request.GET.get('premium')

        strategies_filter = Q(is_live=True, premium__in=['Free', 'Elite', 'Premium']) | Q(is_live=True, premium='VIP', created_by=request.user)
        if request.user.is_superuser:
            strategies_filter = Q()

        if request.user:
            profile_user = request.user_profile

            access_response = profile_user.give_tradingview_access(strategy_id, access=True)

            print("Access response:", access_response)
        
            if access_response.get('error'):
                error = access_response.get('error')

                if pg == "st":
                    context = access_response

                    response = render(request, 'include/user_connect.html', context)
                    return response
                    # response = render(request, 'include/get_access_model.html', context)
                    # return retarget(response, "#access-mb-" + str(strategy_id))
                else:
                    strategies = Strategy.objects.filter(premium=premium, is_live=True)
                    return render(request, 'include/access_list_strategies.html', context = {"strategies": strategies, "error_id": strategy_id, "error": error, "premium": premium})

        if pg == "st":
            context = access_response
            response = render(request, 'include/user_connect.html', context)
            return response
        else:
            strategies = Strategy.objects.filter(premium=premium, is_live=True)
            return render(request, 'include/access_list_strategies.html', context = {"strategies": strategies, "premium": premium})

    except Exception as e:
        print("Error in get_access:", e)
        error = "An unexpected error occurred while granting access. Please try again later."
        strategies = Strategy.objects.filter(premium=premium, is_live=True)
        return render(request, 'include/access_list_strategies.html', context = {"strategies": strategies, "premium": premium, "error": error, "error_id": strategy_id})
    

@require_http_methods(["POST"])
@login_required(login_url='login')
def create_setup_intent(request):
    """
    API endpoint to create a Stripe SetupIntent for the logged-in user and return its client_secret.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        to_add = data.get('to_add', False)

        setup_intent = create_user_setup_intent(request.user_profile, to_add=to_add)
        return JsonResponse({"clientSecret": setup_intent.client_secret})
    except Exception as e:
        print("Error creating setup intent:", e)
        return JsonResponse({"error": str(e)}, status=400)

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

        user_profile = request.user_profile

        try:
            print("Adding payment method ...", payment_method)
            set_to_default = True if len(request.payment_methods) <= 1 else False
            
            payment_methods, user_profile = add_user_payment_method(user_profile, payment_method, set_to_default)

            context["user_profile"] = user_profile
            context["payment_methods"] = payment_methods

            response = render(request, 'include/payment_methods.html', context)
            return retarget(response, "#setting-payment_methods")
        
        except Exception as e:
            context["error"] = str(e)
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

        user_profile = request.user_profile

        try:
            payment_methods, user_profile = delete_user_payment_method(user_profile, payment_method)

            context["user_profile"] = user_profile
            context["payment_methods"] = payment_methods

            response = render(request, 'include/payment_methods.html', context)
            return retarget(response, "#setting-payment_methods")
        
        except Exception as e:
            context["error"] = str(e)

            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-delete-payment_methods")

@require_http_methods([ "POST"])
def setdefault_payment_method(request):
    if request.method == 'POST':
        data = request.POST
        
        try:
            context = {"error": '', 'payment_methods' : request.payment_methods }
            payment_method = data['pm_id']

            if not payment_method:
                context["error"] = 'No payment method has been detected.'

            user_profile = request.user_profile

            customer, user_profile = set_user_default_payment_method(user_profile, payment_method)      

            context["stripe_customer"] = customer
            context["user_profile"] = user_profile

            response = render(request, 'include/payment_methods.html', context)
            return retarget(response, "#setting-payment_methods")
        
        except Exception as e:
            context["error"] = 'Attached payment to customer '+str(e)

            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-delete-payment_methods")

@require_http_methods([ "POST"])
def pay_remaining_amount(request):
    if request.method == 'POST':
        data = request.POST
        
        try:
            context = {"error": '', 'payment_methods' : None}
            payment_method = data['pm_id']

            if not payment_method:
                context["error"] = 'No payment method has been detected.'
                response = render(request, 'include/errors.html', context)
                return retarget(response, "#stripe-error-pay_remaining_amount")

            user_profile = request.user_profile

            user_profile = user_profile.pay_remaining_amount(payment_method=payment_method)

            response = HttpResponse()
            response['HX-Refresh'] = 'true'
            return response
        except Exception as e:
            context["error"] = str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-pay_remaining_amount")

@require_http_methods([ "POST"])
def check_coupon(request):
    if request.method == 'POST':
        data = request.POST

        plan_id = request.GET.get('plan','')
        price_id = PRICE_LIST.get(plan_id, plan_id)

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
                customer_id = request.user_profile.customer_id_value
                price, coupon_off, promo_id = check_coupon_fn(request.user_profile, coupon_id, price)

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

            
            trial_days = request.free_trial_days
            if request.user_profile.subscription_id:
                trial_days = 0

            trial_ends = datetime.datetime.now() + datetime.timedelta(days=trial_days)
            if trial_ends <= datetime.datetime.now() or plan_id == "LIFETIME":
                trial_ends = None
            # print("Trial ends ... ", trial_ends)

            
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
def subscription_stripeform(request):
    if request.method == 'POST':
        data = request.POST

        plan_id = request.GET.get('plan','')
        price_id = PRICE_LIST.get(plan_id, '')

        context = {"error": '', 'title': plan_id}

        if not price_id:
            context["error"] = 'No plan has been specified, please refresh the page and try again.'
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])

        orig_price = float(PRICES.get(plan_id, 0))
        price = orig_price
        
        payment_method = data['pm_id']
        coupon_id = data['coupon']

        user_profile = request.user_profile
        

        if coupon_id:
            try:
                price, price_off, promo_id = check_coupon_fn(user_profile, coupon_id, price)
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

        print("Creating subscription ...")
        
        try:
            lifetime_params = None

            if plan_id == "LIFETIME":
                lifetime_params = {
                    'is_lifetime': True,
                    "price": price,
                    "currency": "usd",
                    "description": "Lifetime subscription.",
                }

            subscription, old_subscription_deleted, user_profile = subscribe_to_main_membership(
                user_profile=user_profile,
                price_id=price_id,
                payment_method=payment_method,
                free_trial_days=request.free_trial_days,
                promo_id=promo_id,
                is_lifetime=lifetime_params
            )


            if lifetime_params:
                print("New lifetime has been created ...")
                send_new_lifetime_email_task(request.user.email)
            else:
                print("New subscription has been created ...", subscription.id)
                if not old_subscription_deleted:
                    send_new_member_email_task(request.user.email)

            # Handle free-trial UI if requested
            from_get_started = request.GET.get('get_started', '')
            if from_get_started == "true":
                context["step"] = 2
                context["congrate"] = True
                response = render(request, 'include/home_get_started.html', context)
                return retarget(response, "#home-get-started")

            return HttpResponseClientRedirect(reverse('membership') + '?sub=True')

        except Exception as e:
            context["error"] = 'Subscription failed. ' + str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#stripe-error-"+context['title'])

@require_http_methods([ "POST"])
def cancel_subscription(request):
    if request.method == 'POST':
        subscription = request.subscription
        user_profile = request.user_profile
        subscription_id = subscription.get('id', None)

        context = {'subscription': subscription_object(subscription), 'error': "" } 

        if subscription_id:
            try:
                subscription, user_profile = cancel_reactivate_subscription(user_profile, subscription_id)
                context['subscription'] = subscription

                if subscription and subscription.get('cancel_at_period_end', False):
                    send_cancel_membership_email_task(request.user.email)

                return render(request, 'include/settings/membership.html', context)
            except Exception as e:
                context['error'] = 'An error occurred while attempting to cancel your subscription. Please contact us for assistance. \n' + str(e)

        return render(request, 'include/settings/membership.html', context)


@login_required(login_url='login')
def complete_seller_account_onboarding(request):
    try:
        profile_user = request.user_profile
        referer_url = request.META.get('HTTP_REFERER')
        
        account_id = profile_user.get_seller_account_id()
        if not account_id:
            messages.error(request, "No seller account found. Please contact support.")
            return redirect(referer_url if referer_url else 'home')

        return_url = referer_url if referer_url else request.build_absolute_uri(reverse('home'))
        refresh_url = referer_url if referer_url else request.build_absolute_uri(reverse('home'))
        
        redirect_obj = get_seller_account_link(account_id, refresh_url, return_url)

        if not redirect_obj or not redirect_obj.url:
            messages.error(request, "Failed to create onboarding link. Please contact support.")
            return redirect(referer_url if referer_url else 'home')

        print("Redirecting to:", redirect_obj.url)
        return HttpResponseRedirect(redirect_obj.url)
    except Exception as e:
        print("Error completing seller onboarding:", e)
        messages.error(request, "An error occurred while completing seller onboarding. Please try again later.")
        return redirect(referer_url if referer_url else 'home')

@login_required
def stripe_seller_dashboard(request):
    try:
        profile_user = request.user_profile
        referer_url = request.META.get('HTTP_REFERER')

        account_id = profile_user.get_seller_account_id()
        if not account_id:
            messages.error(request, "No seller account found. Please contact support.")
            return redirect(referer_url if referer_url else 'home')

        dashboard_link = get_seller_login_link(account_id)

        if not dashboard_link or not dashboard_link.url:
            messages.error(request, "Failed to create dashboard link. Please contact support.")
            return redirect(referer_url if referer_url else 'home')

        print("Redirecting to:", dashboard_link.url)
        return HttpResponseRedirect(dashboard_link.url)
    except Exception as e:
        print("Error accessing seller dashboard:", e)
        messages.error(request, "An error occurred while accessing the seller dashboard. Please try again later.")
        return redirect(referer_url if referer_url else 'home')
        
def preview_email(request):
    # Dummy data for template context
    from profile_user.utils.send_mails import email_context
    context = {'strategy_name': 'Test User', 'strategy_type': 'Elite', **email_context()}
    return render(request, 'emails/new_strategy.html', context)

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

    try:
        wbh = handle_stripe_webhook(User_Profile, Strategy, StrategySubscriber, payload, sig_header)
        status = 200
        if wbh.get('status') == 'error' or wbh.get('status') == 'failed' or wbh.get('status') == 'ignored':
            status = 400
        return JsonResponse(wbh, status=status)

    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def stripe_webhook_connect(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    try:
        wbh = handle_stripe_webhook_connect(User_Profile, Strategy, StrategySubscriber, payload, sig_header)
        status = 200
        if wbh.get('status') == 'error' or wbh.get('status') == 'failed' or wbh.get('status') == 'ignored':
            status = 400
        return JsonResponse(wbh, status=status)

    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({"error": str(e)}, status=400)