from django.shortcuts import render, get_object_or_404
from django.http import Http404

from .models import *

def get_strategies(request):
    subscription = request.subscription
    subscription_period_end = request.subscription_period_end
    subscription_plan = request.subscription_plan
    subscription_status = request.subscription_status

    strategies = Strategy.objects.all()
    context =  {'strategies': strategies, 'subscription': subscription, 'subscription_period_end': subscription_period_end, 'subscription_plan': subscription_plan, 'subscription_status': subscription_status}
    return render(request, 'strategies.html', context)

def get_strategy(request, id):
    strategy = {}
    comments = {}
    results = {}
    subscription = request.subscription
    subscription_period_end = request.subscription_period_end
    subscription_plan = request.subscription_plan
    subscription_status = request.subscription_status

    try:
        strategy = get_object_or_404(Strategy, pk=id)
        comments = strategy.strategycomments_set.all()
        results = strategy.strategyresults_set.all()
    except Strategy.DoesNotExist:
        raise Http404("The object does not exist.")
    
    context =  {'strategy': strategy, 'results': results, 'comments': comments, 'subscription': subscription, 'subscription_period_end': subscription_period_end, 'subscription_plan': subscription_plan, 'subscription_status': subscription_status}
    return render(request, 'strategy.html', context)

def new_result(request):
    pass

def new_comment(request):
    pass