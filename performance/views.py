from django.shortcuts import render
from performance.functions.context import *

# Create your views here.

def get_asset_performance(request, asset, perf_id):
    context = {
        'asset': asset,
    }
    perf = get_asset_performance_context(asset, perf_id)
    if perf is None:
        context['perf_emsg'] = 'No performance data available for this asset.'
    else:
        context.update(perf)

    return render(request, 'performance/asset_performance.html', context)


def get_strategy_performance(request, strategy_id, perf_id):
    strategy = Strategy.objects.get(id=strategy_id)
    if strategy is None:
        context['perf_emsg'] = 'This strategy does not exist.'
    context = {
        'strategy': strategy,
    }
    perf = get_strategy_performance_context(strategy_id, perf_id)
    if perf is None:
        context['perf_emsg'] = 'No performance data available for this strategy.'
    else:
        context.update(perf)

    return render(request, 'performance/strategy_performance.html', context)