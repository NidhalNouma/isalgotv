from django.shortcuts import render
from performance.functions.context import *
from automate.models import CryptoBrokerAccount, ForexBrokerAccount

# Create your views here.

def get_asset_performance(request, asset, perf_id):
    context = {}
    perf = get_asset_performance_context(asset, perf_id)
    if perf is None:
        context['perf_emsg'] = 'No performance data available for this asset.'
    else:
        context.update(perf)

    inpage = request.GET.get('inpage', False)
    if inpage:
        return render(request, 'include/dash/st_performance.html', context=context)
    return render(request, 'performance/asset_performance.html', context)


def get_strategy_performance(request, strategy_id, perf_id):
    strategy = Strategy.objects.get(id=strategy_id)
    if strategy is None:
        context['perf_emsg'] = 'This strategy does not exist.'
    context = {}
    perf = get_strategy_performance_context(strategy_id, perf_id)
    if perf is None:
        context['perf_emsg'] = 'No performance data available for this strategy.'
    else:
        context.update(perf)

    inpage = request.GET.get('inpage', False)
    if inpage:
        return render(request, 'include/dash/st_performance.html', context=context)
    return render(request, 'performance/strategy_performance.html', context)


def get_strategy_asset_performance(request, strategy_perf_id, asset_perf_id):
    context = {
        'strategy_perf_id': strategy_perf_id,
        'asset_perf_id': asset_perf_id,
    }
    
    perf = get_strategy_asset_performance_context(strategy_perf_id, asset_perf_id)
    if perf is None:
        context['perf_emsg'] = 'No performance data available for this strategy and asset combination.'
    else:
        context.update(perf)
    inpage = request.GET.get('inpage', False)
    if inpage:
        return render(request, 'include/dash/st_performance.html', context=context)
    return render(request, 'performance/strategy_asset_performance.html', context=context)


def get_account_performance(request, public_id):
    # Get the account (crypto or forex)
    crypto_account = CryptoBrokerAccount.objects.filter(public_id=public_id).first()
    if crypto_account:
        account = crypto_account
    else:
        forex_account = ForexBrokerAccount.objects.filter(public_id=public_id).first()
        if forex_account:
            account = forex_account
        else:
            return render(request, "404.html", status=404)

    account_perf_context = account_context_data(account)

    if account_perf_context is None:
        return render(request, "404.html", status=404)

    context = {
        'account': account,
        'id': account.id,
        'broker_type': account.broker_type,
        **account_perf_context
    }

    return render(request, "performance/account_perfromance.html", context=context)
