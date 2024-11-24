from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django_htmx.http import retarget, trigger_client_event, HttpResponseClientRedirect

from .functions.binance import check_binance_credentials
from .models import *
from .forms import *


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
                'created_by' : request.user.user_profile,
                'broker_type': broker_type
            }
            form = AddCryptoBrokerAccountForm(form_data) 

            if form.is_valid():
                valid = check_binance_credentials(form_data.get('apiKey'), form_data.get('secretKey'), form_data.get('type'))
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
                    print(form.errors)
                    response = render(request, "include/errors.html", context=context)
                    return retarget(response, f'#add-{broker_type}-form-errors')
                
            else:
                context = {'error': form.errors}
                print(form.errors)
                response = render(request, "include/errors.html", context=context)
                return retarget(response, f'#add-{broker_type}-form-errors')

    except Exception as e:
        print(e)
        # context = {'error': e}
        context = {'error': "An error occurred while adding this account."}
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
                    print(form.errors)
                    response = render(request, "include/errors.html", context=context)
                    return retarget(response, f'#edit-{account.id}_{account.broker_type}-form-errors')
                
            else:
                context = {'error': form.errors}
                print(form.errors)
                response = render(request, "include/errors.html", context=context)
                return retarget(response, f'#edit-{account.id}_{account.broker_type}-form-errors')

    except Exception as e:
        print(e)
        # context = {'error': e}
        context = {'error': "An error occurred while editing this account."}
        response = render(request, "include/errors.html", context=context)
        return retarget(response, f'#edit-{account.id}_{account.broker_type}-form-errors')

@require_http_methods([ "POST"])
def toggle_crypto_broker(request, pk):
    model_instance = CryptoBrokerAccount.objects.get(pk=pk)

    model_instance.active = not model_instance.active
    model_instance.save()

    context = context_accounts_by_user(request)
    return render(request, 'include/accounts_list.html', context=context)

@require_http_methods([ "POST"])
def delete_crypto_broker(request, pk):
    response = CryptoBrokerAccount.objects.delete(pk=pk) 

    print(response)

    context = context_accounts_by_user(request)
    return render(request, 'include/accounts_list.html', context=context)

