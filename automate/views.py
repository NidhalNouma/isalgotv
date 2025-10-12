from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.contrib.contenttypes.models import ContentType

from django_htmx.http import retarget, trigger_client_event, HttpResponseClientRedirect
from django.views.decorators.csrf import csrf_exempt

from automate.functions.alerts_logs_trades import check_crypto_credentials, check_forex_credentials
from automate.functions.alerts_message import manage_alert
from automate.models import *
from automate.forms import *
from automate.tasks import *

from automate.functions.brokers.metatrader import MetatraderClient
from automate.functions.brokers.ctrader import CLIENT_ID

from collections import defaultdict
from django.utils.timezone import localtime

from asgiref.sync import sync_to_async, async_to_sync

import environ
env = environ.Env()

import requests
import datetime
import stripe

stripe.api_key = env('STRIPE_API_KEY')
stripe_wh_secret = env('STRIPE_API_WEBHOOK_SECRET')

from django.conf import settings
PRICE_LIST = settings.PRICE_LIST
PRICES = settings.PRICES



def context_accounts_by_user(request):
    user_profile = request.user.user_profile  
    crypto_accounts = list(CryptoBrokerAccount.objects.filter(created_by=user_profile))
    forex_accounts = list(ForexBrokerAccount.objects.filter(created_by=user_profile))

    # Annotate each account with its broker type
    for acc in crypto_accounts:
        acc.broker = 'crypto'
    for acc in forex_accounts:
        acc.broker = 'forex'

    # Combine and sort all accounts by created_at descending
    all_accounts = crypto_accounts + forex_accounts
    all_accounts.sort(key=lambda x: x.created_at, reverse=True)

    context = {
        'accounts': all_accounts,
        'ctrader_client_id': CLIENT_ID,
    }
    return context


def index(request):
    # Ensure the user is logged in
    if not request.user.is_authenticated:
        return render(request, "automate/automate.html", context={})
    
    return render(request, "automate/automate.html", context=context_accounts_by_user(request))

def webhook_404(request, exception):
    return HttpResponse("Page not found!", content_type="text/plain")

@require_http_methods(["GET"])
def ctrader_auth_code(request):
    # Extract the 'code' parameter from the GET request
    auth_code = request.GET.get('code', None)

    context = {
        "auth_code": auth_code,
        "error": None if auth_code else "Authorization code not found in the request."
    }

    return render(request, "automate/ctrader_auth_code.html", context=context)

@require_http_methods([ "POST"])
def add_broker(request, broker_type):
    try:
        if request.method == 'POST':

            crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
            forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

            payment_method = request.POST.get('pm_id')

            if not payment_method or payment_method == "None":
                response = render(request, 'include/errors.html', {'error': 'No payment method has been detected.'})
                return retarget(response, f'#add-{broker_type}-form-errors')

            if broker_type in crypto_broker_types:
                form_data = {
                    'name': request.POST.get(f'{broker_type}_name'),
                    'apiKey': request.POST.get(f'{broker_type}_apiKey'),
                    'secretKey': request.POST.get(f'{broker_type}_secretKey'),
                    'type': request.POST.get(f'{broker_type}_type'),
                    'pass_phrase': request.POST.get(f'{broker_type}_pass_phrase'),
                    'created_by' : request.user.user_profile,
                    'broker_type': broker_type
                }
                form = AddCryptoBrokerAccountForm(form_data) 

            elif broker_type in forex_broker_types:
                form_data = {
                    'name': request.POST.get(f'{broker_type}_name'),
                    'username': request.POST.get(f'{broker_type}_username'),
                    'password': request.POST.get(f'{broker_type}_password'),
                    'server': request.POST.get(f'{broker_type}_server'),
                    'type': request.POST.get(f'{broker_type}_type', 'D'),
                    'created_by' : request.user.user_profile,
                    'broker_type': broker_type
                }

                if broker_type == 'ctrader':
                    form_data['username'] = 'xxx'
                    form_data['password'] = 'xxx'
                form = AddForexBrokerAccountForm(form_data) 

            else:
                raise Exception("Invalid Broker Type")

            if form.is_valid():

                if broker_type in crypto_broker_types:
                    valid = check_crypto_credentials(broker_type ,form_data.get('apiKey'), form_data.get('secretKey'), form_data.get('pass_phrase', ""), form_data.get('type'))

                elif broker_type in forex_broker_types:
                    valid = check_forex_credentials(broker_type ,form_data.get('username'), form_data.get('password'), form_data.get('server'), form_data.get('type'))

                print(valid)
                if valid.get('valid') == True:
                    # Add a subscription
                    profile_user = request.user_profile
                    customer_id = profile_user.customer_id_value

                    stripe.PaymentMethod.attach(
                        payment_method,
                        customer=customer_id,
                    )

                    price_id = PRICE_LIST.get('CRYPTO', '')
                    if broker_type in forex_broker_types:
                        price_id = PRICE_LIST.get('FOREX', '')
                    if broker_type == 'metatrader4' or broker_type == 'metatrader5':
                        price_id = PRICE_LIST.get('METATRADER', '')

                    metadata = {
                        "profile_user_id": str(profile_user.id), 
                        "broker_type": broker_type,
                    }
                    
                    subscription = stripe.Subscription.create(
                        customer=customer_id,
                        items=[{
                            'price': price_id,
                        }],
                        default_payment_method=payment_method,
                        payment_behavior="error_if_incomplete",
                        trial_settings={"end_behavior": {"missing_payment_method": "pause"}},
                        metadata=metadata
                    )


                    account = form.save(commit=False)
                    account.subscription_id = subscription.id

                    if valid.get('account_api_id'):
                        account.account_api_id = valid.get('account_api_id')
                    
                    if valid.get('ctrader_access_token'):
                        account.server = valid.get('ctrader_access_token')
                        account.username = valid.get('account_id', 'xxx')

                    if valid.get('account_type'):
                        account_type = valid.get('account_type')
                        account.type = 'L' if str(account_type).lower() in ('live', 'l') else 'D'

                    account.save()

                    context = context_accounts_by_user(request)

                    context["trigger_modal"] = f'add-{broker_type}-modal'
                    context["trigger_btn"] = f'-add-{broker_type}'
                    return render(request, 'include/accounts_list.html', context=context)
                
                else: 
                    if broker_type == 'metatrader4' or broker_type == 'metatrader5':
                        if valid.get('account_api_id'):
                            account_obj = ForexBrokerAccount(**valid) 
                            delete_account = MetatraderClient(account=account_obj).delete_account()

                    raise Exception(valid.get('error'))
                
            else:
                raise Exception(form.errors)

    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        return retarget(response, f'#add-{broker_type}-form-errors')

@require_http_methods([ "POST"])
def edit_broker(request, broker_type, pk):
    try:
        if request.method == 'POST':

            crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
            forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]


            if broker_type == "metatrader4" or broker_type == "metatrader5":
                raise Exception("Editing of Metatrader accounts is not allowed directly. Please delete and re-add the account if needed.")

            if broker_type in crypto_broker_types:
                account = CryptoBrokerAccount.objects.get(pk=pk)

                form_data = {
                    'name': request.POST.get(f'{account.id}_{account.broker_type}_name'),
                    'apiKey': request.POST.get(f'{account.id}_{account.broker_type}_apiKey'),
                    'secretKey': request.POST.get(f'{account.id}_{account.broker_type}_secretKey'),
                    'pass_phrase': request.POST.get(f'{account.id}_{broker_type}_pass_phrase'),
                    'type': request.POST.get(f'{account.id}_{account.broker_type}_type'),
                    'created_by' : request.user.user_profile,
                    'broker_type': account.broker_type
                }
                form = AddCryptoBrokerAccountForm(form_data, instance=account) 

            elif broker_type in forex_broker_types:
                account = ForexBrokerAccount.objects.get(pk=pk)
                form_data = {
                    'name': request.POST.get(f'{account.id}_{account.broker_type}_name'),
                    'username': request.POST.get(f'{account.id}_{account.broker_type}_username'),
                    'password': request.POST.get(f'{account.id}_{account.broker_type}_password'),
                    'server': request.POST.get(f'{account.id}_{account.broker_type}_server'),
                    'type': request.POST.get(f'{account.id}_{account.broker_type}_type', 'D'),
                    'created_by' : request.user.user_profile,
                    'broker_type': broker_type
                }
                if broker_type == 'ctrader':
                    form_data['username'] = 'xxx'
                    form_data['password'] = 'xxx'
                form = AddForexBrokerAccountForm(form_data, instance=account) 
            else:
                raise Exception("Invalid Broker Type")

            if form.is_valid():
                if broker_type in crypto_broker_types:
                    valid = check_crypto_credentials(broker_type, form_data.get('apiKey'), form_data.get('secretKey'), form_data.get('pass_phrase'), form_data.get('type'))

                elif broker_type in forex_broker_types:
                    valid = check_forex_credentials(broker_type, form_data.get('username'), form_data.get('password'), form_data.get('server'), form_data.get('type'))

                if valid.get('valid') == True:
                    if not account.subscription_id:
                        raise Exception("No subscription found.")
                    
                    subscription = stripe.Subscription.retrieve(account.subscription_id)

                    if not subscription or subscription.status != "active":
                        raise Exception("Subscription is not active. Please activate your subscription.")

                    if valid.get('account_api_id'):
                        account.account_api_id = valid.get('account_api_id')
                    
                    if valid.get('ctrader_access_token'):
                        account.server = valid.get('ctrader_access_token')
                        account.username = valid.get('account_id', 'xxx')

                    if valid.get('account_type'):
                        account_type = valid.get('account_type')
                        account.type = 'L' if str(account_type).lower() in ('live', 'l') else 'D'
                    
                    account = form.save(commit=False)
                    
                    account.subscription_id = subscription.id
                    account.save()

                    context = context_accounts_by_user(request)
                    context["trigger_modal"] = f'edit-{pk}-{account.broker_type}-modal'
                    return render(request, 'include/accounts_list.html', context=context)
                
                else: 
                    context = {'error': valid.get('error')}
                    response = render(request, "include/errors.html", context=context)
                    return retarget(response, f'#edit-{account.id}_{account.broker_type}-form-errors')
                
            else:
                context = {'error': form.errors}
                response = render(request, "include/errors.html", context=context)
                return retarget(response, f'#edit-{account.id}_{account.broker_type}-form-errors')

    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        return retarget(response, f'#edit-{pk}_{broker_type}-form-errors')

@require_http_methods([ "POST"])
def toggle_broker(request, broker_type, pk):

    try:
        crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
        forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

        if broker_type in crypto_broker_types:
            model_instance = CryptoBrokerAccount.objects.get(pk=pk)
        elif broker_type in forex_broker_types:
            model_instance = ForexBrokerAccount.objects.get(pk=pk)
        else:
            raise Exception("Invalid Broker Type")

        model_instance.active = not model_instance.active

        if broker_type == "metatrader4" or broker_type == "metatrader5":
            # Undeploy/Deploy the account
            deploy_undeploy = MetatraderClient(account=model_instance).deploy_undeploy_account(deploy=model_instance.active)
            if "error" in deploy_undeploy:
                raise Exception(f"Failed to {'deploy' if model_instance.active else 'undeploy'} metatrader account: {deploy_undeploy['error']}")

        if model_instance.subscription_id:
            if not model_instance.active:
                # Pause the subscription by setting the status to "paused"
                stripe.Subscription.modify(
                    model_instance.subscription_id,
                    pause_collection={"behavior": "keep_as_draft"}
                )
            else:
                # Resume by setting it back to "active"
                stripe.Subscription.modify(
                    model_instance.subscription_id,
                    pause_collection=''
                )

        model_instance.save()

        context = context_accounts_by_user(request)
        return render(request, 'include/accounts_list.html', context=context)

    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        return retarget(response, f'#{broker_type}-account-activate-{pk}-form-errors')

@require_http_methods([ "POST"])
def delete_broker(request, broker_type, pk):
    try:
        crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
        forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

        if broker_type in crypto_broker_types:
            obj = CryptoBrokerAccount.objects.get(pk=pk)
            if obj.subscription_id:
                stripe.Subscription.cancel(obj.subscription_id)
                # stripe.Subscription.modify(
                #     obj.subscription_id,
                #     cancel_at_period_end=True  # Subscription will be canceled but remain active until the next billing cycle
                # )
            obj.delete()  
        elif broker_type in forex_broker_types:
            obj = ForexBrokerAccount.objects.get(pk=pk)

            if broker_type == "metatrader4" or broker_type == "metatrader5":
                delete_response = MetatraderClient(account=obj).delete_account()
                if "error" in delete_response:
                    raise Exception(f"Failed to delete metatrader account: {delete_response['error']}")

            if obj.subscription_id:
                stripe.Subscription.cancel(obj.subscription_id)
                # stripe.Subscription.modify(
                #     obj.subscription_id,
                #     cancel_at_period_end=True 
                # )

            obj.delete()
        else:
            raise Exception("Invalid Broker Type")

        context = context_accounts_by_user(request)
        return render(request, 'include/accounts_list.html', context=context)
    
    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        return retarget(response, f'#{broker_type}-account-activate-{pk}-form-errors')


def account_subscription_context(broker_type, pk, subscription_id):
    subscription = stripe.Subscription.retrieve(subscription_id)

    payment_method = None
    if subscription.default_payment_method:
        payment_method = stripe.PaymentMethod.retrieve(subscription.default_payment_method)
        payment_method = [payment_method]
    
    end_timestamp = subscription.current_period_end * 1000
    next_payment_date = datetime.datetime.fromtimestamp(end_timestamp / 1e3)
    subscription_active = subscription.plan.active
    subscription_status = subscription.status

    subscription_paused = False  
    if subscription.pause_collection:
        subscription_paused = True if subscription.pause_collection.behavior == 'keep_as_draft' else False

    context = {
        'account_subscription': subscription,
        'pm': payment_method,
        'subscription_paused': subscription_paused,
        'subscription_active': subscription_active,
        'subscription_status': subscription_status,
        'next_payment_date': next_payment_date,
        'subscription_next_payment_amount': subscription.plan.amount / 100,
        'broker_type': broker_type,
        'id': str(pk),
    }

    # print(context)
    return context


@require_http_methods([ "POST"])
def account_subscription_data(request, broker_type, pk, account_subscription_id):
    try:
        context = account_subscription_context(broker_type, pk, account_subscription_id)

        return render(request, 'include/edit_broker_membership.html', context=context)
    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        
        return retarget(response, f'#edit-{pk}_{broker_type}-sub-errors') 


@require_http_methods([ "POST"])
def change_account_subscription_payment(request, broker_type, pk, account_subscription_id):
    try:
        new_payment_method = request.POST.get("pm_id")  
        if not new_payment_method:
            raise Exception("No payment method provided.")

        subscription = stripe.Subscription.retrieve(account_subscription_id)
        
        # stripe.PaymentMethod.attach(
        #     new_payment_method,
        #     customer=subscription.customer,
        # )

        if subscription.status == "canceled":
            # stripe.Subscription.create

            profile_user = request.user_profile
            customer_id = profile_user.customer_id_value

            stripe.PaymentMethod.attach(
                new_payment_method,
                customer=customer_id,
            )

            crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
            forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

            price_id = PRICE_LIST.get('CRYPTO', '')
            if broker_type in forex_broker_types:
                broker = ForexBrokerAccount.objects.get(subscription_id=account_subscription_id)
                price_id = PRICE_LIST.get('FOREX', '')
            else:
                broker = CryptoBrokerAccount.objects.get(subscription_id=account_subscription_id)
                price_id = PRICE_LIST.get('CRYPTO', '')

            metadata = {
                "profile_user_id": str(profile_user.id), 
                "broker_type": broker_type,
            }
            
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': price_id,
                }],
                default_payment_method=new_payment_method,
                payment_behavior="error_if_incomplete",
                trial_settings={"end_behavior": {"missing_payment_method": "pause"}},
                metadata=metadata
            )
            account_subscription_id = subscription.id
            broker.subscription_id = account_subscription_id
            broker.save()

        else:
            # Update the default payment method for the subscription
            stripe.Subscription.modify(
                account_subscription_id,
                default_payment_method=new_payment_method,
            )

        context = account_subscription_context(broker_type, pk, account_subscription_id)

        return render(request, 'include/edit_broker_membership.html', context=context)
    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        
        return retarget(response, f'#add-{broker_type}-account_subscription_pm{pk}-form-errors') 
    
# TODO: Send Email when account is turned off
def account_subscription_failed(email ,broker_type, subscription_id, send_mail=True):
    try:
        crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
        forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

        if broker_type in crypto_broker_types:
            obj = CryptoBrokerAccount.objects.filter(subscription_id=subscription_id).first()
            if obj:
                obj.active = False
                obj.save()
                if send_mail and email:
                    send_broker_account_access_removed_task(email, obj.name)
            else:
                print(f"No CryptoBrokerAccount found for subscription_id {subscription_id}")
                if send_mail and email:
                    send_broker_account_deleted_task(email)
        elif broker_type in forex_broker_types:
            obj = ForexBrokerAccount.objects.filter(subscription_id=subscription_id).first()
            if obj:
                if broker_type == "metatrader4" or broker_type == "metatrader5":
                    # Undeploy the account
                    MetatraderClient(account=obj).deploy_undeploy_account(deploy=False)

                obj.active = False
                obj.save()
                if send_mail and email:
                    send_broker_account_access_removed_task(email, obj.name)
            else:
                print(f"No ForexBrokerAccount found for subscription_id {subscription_id}")
                if send_mail and email:
                    send_broker_account_deleted_task(email)
        else:
            raise Exception("Invalid Broker Type")

    except Exception as e:
        print(e)

@require_http_methods([ "GET"])
def get_broker_logs(request, broker_type, pk):
    try:
        # Pagination parameters (per date now)
        start = int(request.GET.get('start', 0))
        limit = 40  # number of days per page

        crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
        forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

        if broker_type in crypto_broker_types:
            account_model = CryptoBrokerAccount
        elif broker_type in forex_broker_types:
            account_model = ForexBrokerAccount
        else:
            raise ValueError("Invalid Broker Type")

        content_type = ContentType.objects.get_for_model(account_model)

        logs_qs = LogMessage.objects.filter(
            content_type=content_type, object_id=pk
        ).order_by('-created_at')

        # Apply pagination directly at query level
        logs_list = logs_qs[start:start+limit]
        
        total = logs_qs.count()   # still get total count for pagination

        next_start = start + limit if start + limit < total else None

        context = {
            'logs': logs_list,
            'id': pk,
            'broker_type': broker_type,
            'next_start': next_start,
        }

        if start == 0:
            return render(request, 'include/account_logs.html', context=context)
        else:
            return render(request, 'include/account_logs_list.html', context=context)

    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        return response
    
    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        return response


def get_accounts_list_json(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            accounts = context_accounts_by_user(request)
            crypto_accounts = [
                {
                    "id": acc.id,
                    "broker_type": acc.broker_type,
                    "type": acc.type,
                    "name": acc.name,
                    "active": acc.active,
                }
                for acc in accounts.get('crypto_accounts', [])
            ]

            forex_accounts = [
                {
                    "id": acc.id,
                    "broker_type": acc.broker_type,
                    "type": acc.type,
                    "name": acc.name,
                    "active": acc.active,
                }
                for acc in accounts.get("forex_accounts", [])
            ]

            return JsonResponse({"success": True, "crypto_accounts": crypto_accounts, 'forex_accounts': forex_accounts})

@require_http_methods(["GET"])
def get_broker_trades(request, broker_type, pk):
    try:
        # Pagination parameters
        start = int(request.GET.get('start', 0))
        limit = 30

        crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
        forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

        if broker_type in crypto_broker_types:
            account_model = CryptoBrokerAccount
        elif broker_type in forex_broker_types:
            account_model = ForexBrokerAccount
        else:
            raise ValueError("Invalid Broker Type")

        content_type = ContentType.objects.get_for_model(account_model)
        all_trades = TradeDetails.objects.filter(content_type=content_type, object_id=pk).order_by('-exit_time')
        trade_list = all_trades[start:start+limit]

        # Determine next start offset for pagination
        total = all_trades.count()
        next_start = start + limit if start + limit < total else None

        context = {
            'trades': trade_list,
            'id': pk,
            'broker_type': broker_type,
            'next_start': next_start,
        }
        if start == 0:
            return render(request, 'include/account_trades.html', context=context)
        else:
            return render(request, 'include/account_trades_tablebody.html', context=context)
    
    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        return response


@require_http_methods(["POST"])
@csrf_exempt
@async_to_sync
async def handle_webhook_crypto(request, custom_id):
    try:
        # Fetch the account asynchronously
        account = await sync_to_async(CryptoBrokerAccount.objects.get)(custom_id=custom_id)

        if not account.active:
            return JsonResponse({'error': 'Account is not active', "IP": request.META.get('REMOTE_ADDR')}, status=400)
        
        # Serialize the account object
        account_data = {
            'id': account.id,
            'name': account.name,
            'custom_id': account.custom_id,
        }

        # Decode the request body asynchronously
        text_data = request.body.decode('utf-8')

        # Call manage_alert asynchronously if it supports async (or use sync_to_async)
        manage_alert_response = await sync_to_async(manage_alert)(text_data, account)

        response_data = {
            'account': account_data,
            'status': 'success',
            "IP": request.META.get('REMOTE_ADDR'),
            "Server IP": request.server_ip,
            'response': manage_alert_response
        }

        return JsonResponse(response_data, status=200)
    
    except CryptoBrokerAccount.DoesNotExist:
        return JsonResponse({'error': 'Account not found', "IP": request.META.get('REMOTE_ADDR')}, status=404)

@require_http_methods(["POST"])
@csrf_exempt
@async_to_sync
async def handle_webhook_forex(request, custom_id):
    try:
        # Fetch the account asynchronously
        account = await sync_to_async(ForexBrokerAccount.objects.get)(custom_id=custom_id)

        if not account.active:
            return JsonResponse({'error': 'Account is not active', "IP": request.META.get('REMOTE_ADDR')}, status=400)

        # Serialize the account object
        account_data = {
            'id': account.id,
            'name': account.name,
            'custom_id': account.custom_id,
        }

        # Decode the request body asynchronously
        text_data = request.body.decode('utf-8')

        # Call manage_alert asynchronously
        manage_alert_response = await sync_to_async(manage_alert)(text_data, account)

        response_data = {
            'account': account_data,
            'status': 'success',
            "IP": request.META.get('REMOTE_ADDR'),
            "Server IP": request.server_ip,
            'response': manage_alert_response
        }

        return JsonResponse(response_data, status=200)

    except ForexBrokerAccount.DoesNotExist:
        return JsonResponse({'error': 'Account not found', "IP": request.META.get('REMOTE_ADDR')}, status=404)



@require_http_methods(["POST"])
@csrf_exempt
def get_server_ip(request):

    server_ip_req = requests.get('https://ifconfig.me')
    server_ip = server_ip_req.text
    return JsonResponse({'server_ip': server_ip}, status=200)