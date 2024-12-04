from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse

from django_htmx.http import retarget, trigger_client_event, HttpResponseClientRedirect
from django.views.decorators.csrf import csrf_exempt

from .functions.binance import check_binance_credentials
from .functions.alerts_logs_trades import manage_alert, check_credentials
from .models import *
from .forms import *

from collections import defaultdict
from django.utils.timezone import localtime


def context_accounts_by_user(request):
    user_profile = request.user.user_profile  
    crypto_accounts = CryptoBrokerAccount.objects.filter(created_by=user_profile)

    context ={
        'crypto_accounts': crypto_accounts
    }

    return context


def index(request):
    # Ensure the user is logged in
    if not request.user.is_authenticated:
        return render(request, "automate/automate.html", context={})
    
    return render(request, "automate/automate.html", context=context_accounts_by_user(request))

@require_http_methods([ "POST"])
def add_crypto_broker(request, broker_type):
    try:
        if request.method == 'POST':
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

            if form.is_valid():
                valid = check_credentials(broker_type ,form_data.get('apiKey'), form_data.get('secretKey'), form_data.get('pass_phrase'), form_data.get('type'))
                print(valid)

                if valid.get('valid') == True:
                    crypto_account = form.save(commit=False)
                    crypto_account.save()

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
def edit_crypto_broker(request, pk):
    try:
        if request.method == 'POST':

            account = CryptoBrokerAccount.objects.get(pk=pk)

            form_data = {
                'name': request.POST.get(f'{account.id}_{account.broker_type}_name'),
                'apiKey': request.POST.get(f'{account.id}_{account.broker_type}_apiKey'),
                'secretKey': request.POST.get(f'{account.id}_{account.broker_type}_secretKey'),
                'type': request.POST.get(f'{account.id}_{account.broker_type}_type'),
                'created_by' : request.user.user_profile,
                'broker_type': account.broker_type
            }
            form = AddCryptoBrokerAccountForm(form_data, instance=account) 

            if form.is_valid():
                valid = check_binance_credentials(form_data.get('apiKey'), form_data.get('secretKey'), form_data.get('type'))
                print(valid)

                if valid.get('valid') == True:
                    crypto_account = form.save(commit=False)
                    crypto_account.save()

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
def toggle_crypto_broker(request, pk):
    model_instance = CryptoBrokerAccount.objects.get(pk=pk)

    # context = {'error': "An error occurred while editing this account.", 'close': f'crypto-account-activate-{pk}' }
    # response = render(request, "include/errors.html", context=context)
    # return retarget(response, f'#crypto-account-activate-{pk}-form-errors')

    model_instance.active = not model_instance.active
    model_instance.save()

    context = context_accounts_by_user(request)
    return render(request, 'include/accounts_list.html', context=context)

@require_http_methods([ "POST"])
def delete_crypto_broker(request, pk):
    response = CryptoBrokerAccount.objects.delete(pk=pk) 

    # print(response)

    context = context_accounts_by_user(request)
    return render(request, 'include/accounts_list.html', context=context)

@require_http_methods([ "POST"])
def get_crypto_broker_logs(request, pk):
    logs_list = CryptoLogMessage.objects.filter(account_id=pk).order_by('-created_at')
    grouped_logs = defaultdict(list)

    for log in logs_list:
        log_date = localtime(log.created_at).strftime('%Y-%m-%d')  
        grouped_logs[log_date].append(log)

    context = {
        'grouped_logs': dict(grouped_logs),
        'logs': logs_list,
        'id': pk
    }
    
    return render(request, 'include/account_logs.html', context=context)


@require_http_methods([ "POST"])
@csrf_exempt
def handle_webhook_crypto(request, custom_id):
    try:
        account = CryptoBrokerAccount.objects.get(custom_id=custom_id)
        # Serialize the account object (convert to a dictionary)
        account_data = {
            'id': account.id,
            'name': account.name,
            'custom_id': account.custom_id,
            # Include other relevant fields if needed
        }
        response_data = {
            'account': account_data,
            'status': 'success',
            "IP": request.server_ip
        }

        text_data = request.body.decode('utf-8')  # Decode the bytes object to string

        manage_alert_response = manage_alert(text_data, account)

        return JsonResponse(response_data, status=200)
    
    except CryptoBrokerAccount.DoesNotExist:
        return JsonResponse({'error': 'Account not found', "IP": request.server_ip}, status=404)
    
