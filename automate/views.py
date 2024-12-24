from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.contrib.contenttypes.models import ContentType

from django_htmx.http import retarget, trigger_client_event, HttpResponseClientRedirect
from django.views.decorators.csrf import csrf_exempt

from .functions.alerts_logs_trades import manage_alert, check_crypto_credentials, check_forex_credentials
from .models import *
from .forms import *

from collections import defaultdict
from django.utils.timezone import localtime

from asgiref.sync import sync_to_async, async_to_sync



def context_accounts_by_user(request):
    user_profile = request.user.user_profile  
    crypto_accounts = CryptoBrokerAccount.objects.filter(created_by=user_profile)
    forex_accounts = ForexBrokerAccount.objects.filter(created_by=user_profile)

    context ={
        'crypto_accounts': crypto_accounts,
        'forex_accounts': forex_accounts
    }

    return context


def index(request):
    # Ensure the user is logged in
    if not request.user.is_authenticated:
        return render(request, "automate/automate.html", context={})
    
    return render(request, "automate/automate.html", context=context_accounts_by_user(request))

@require_http_methods([ "POST"])
def add_broker(request, broker_type):
    try:
        if request.method == 'POST':

            crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
            forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

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
                    'type': request.POST.get(f'{broker_type}_type'),
                    'created_by' : request.user.user_profile,
                    'broker_type': broker_type
                }
                form = AddForexBrokerAccountForm(form_data) 

            else:
                raise Exception("Invalid Broker Type")

            if form.is_valid():

                if broker_type in crypto_broker_types:
                    valid = check_crypto_credentials(broker_type ,form_data.get('apiKey'), form_data.get('secretKey'), form_data.get('pass_phrase'), form_data.get('type'))

                elif broker_type in forex_broker_types:
                    valid = check_forex_credentials(broker_type ,form_data.get('username'), form_data.get('password'), form_data.get('server'), form_data.get('type'))

                print(valid)
                if valid.get('valid') == True:
                    account = form.save(commit=False)
                    account.save()

                    context = context_accounts_by_user(request)

                    context["trigger_modal"] = f'add-{broker_type}-modal'
                    context["trigger_btn"] = f'-add-{broker_type}'
                    return render(request, 'include/accounts_list.html', context=context)
                
                else: 
                    context = {'error': valid.get('error')}
                    response = render(request, "include/errors.html", context=context)
                    return retarget(response, f'#add-{broker_type}-form-errors')
                
            else:
                context = {'error': form.errors}
                response = render(request, "include/errors.html", context=context)
                return retarget(response, f'#add-{broker_type}-form-errors')

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
                    'type': request.POST.get(f'{account.id}_{account.broker_type}_type'),
                    'created_by' : request.user.user_profile,
                    'broker_type': broker_type
                }
                form = AddForexBrokerAccountForm(form_data, instance=account) 
            else:
                raise Exception("Invalid Broker Type")

            if form.is_valid():
                if broker_type in crypto_broker_types:
                    valid = check_crypto_credentials(broker_type, form_data.get('apiKey'), form_data.get('secretKey'), form_data.get('pass_phrase'), form_data.get('type'))

                elif broker_type in forex_broker_types:
                    valid = check_forex_credentials(broker_type, form_data.get('username'), form_data.get('password'), form_data.get('server'), form_data.get('type'))

                if valid.get('valid') == True:
                    account = form.save(commit=False)
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
        return retarget(response, f'#edit-{account.id}_{account.broker_type}-form-errors')

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
            obj.delete()  
        elif broker_type in forex_broker_types:
            obj = ForexBrokerAccount.objects.get(pk=pk)
            obj.delete()
        else:
            raise Exception("Invalid Broker Type")

        context = context_accounts_by_user(request)
        return render(request, 'include/accounts_list.html', context=context)
    
    except Exception as e:
        context = {'error': e}
        response = render(request, "include/errors.html", context=context)
        return retarget(response, f'#{broker_type}-account-activate-{pk}-form-errors')

@require_http_methods([ "POST"])
def get_broker_logs(request, broker_type, pk):
    try:

        crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
        forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

        if broker_type in crypto_broker_types:
            account_model = CryptoBrokerAccount
        elif broker_type in forex_broker_types:
            account_model = ForexBrokerAccount
        else:
            raise ValueError("Invalid Broker Type")


        content_type = ContentType.objects.get_for_model(account_model)
        logs_list = LogMessage.objects.filter(content_type=content_type, object_id=pk).order_by('-created_at')

        grouped_logs = defaultdict(list)
        for log in logs_list:
            log_date = localtime(log.created_at).strftime('%Y-%m-%d')  
            grouped_logs[log_date].append(log)

        context = {
            'grouped_logs': dict(grouped_logs),
            'logs': logs_list,
            'id': pk,
            'broker_type': broker_type
        }
        
        return render(request, 'include/account_logs.html', context=context)
    
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
