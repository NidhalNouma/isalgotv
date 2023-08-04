from django.shortcuts import render

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
    subscription = request.subscription
    subscription_period_end = request.subscription_period_end
    subscription_plan = request.subscription_plan
    subscription_status = request.subscription_status
    # strategy = Strategy.objects.get(id=strategy_id)
    context =  {'strategy': strategy, 'subscription': subscription, 'subscription_period_end': subscription_period_end, 'subscription_plan': subscription_plan, 'subscription_status': subscription_status}
    return render(request, 'strategy.html', context)

def new_result(request):
    pass

def new_comment(request):
    pass