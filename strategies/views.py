from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, OuterRef, Subquery
from django.http import Http404

from .models import *

def get_strategies(request):
    subscription = request.subscription
    subscription_period_end = request.subscription_period_end
    subscription_plan = request.subscription_plan
    subscription_status = request.subscription_status

    strategies = Strategy.objects.prefetch_related(
            Prefetch('images', queryset=StrategyImages.objects.all())
        )
    
    # print(strategies)

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

    # try:
    #     strategy = get_object_or_404(Strategy, pk=id)
    #     comments = strategy.strategycomments_set.all()
    #     results = strategy.strategyresults_set.all()
    # except Strategy.DoesNotExist:
    #     raise Http404("The object does not exist.")
    try:
        strategy = Strategy.objects.select_related('created_by').prefetch_related(
            'images',
        ).get(pk=id)

        comments = strategy.strategycomments_set.select_related('created_by').prefetch_related(
                'images', Prefetch('replies', queryset=Replies.objects.select_related('created_by').prefetch_related('images')),
            )
        
        results = strategy.strategyresults_set.select_related('created_by').prefetch_related(
                'images', Prefetch('replies', queryset=Replies.objects.select_related('created_by').prefetch_related('images')),
            )
    except Strategy.DoesNotExist:
        raise Http404("The object does not exist.")
    
    context =  {'strategy': strategy, 'results': results, 'comments': comments, 'subscription': subscription, 'subscription_period_end': subscription_period_end, 'subscription_plan': subscription_plan, 'subscription_status': subscription_status}
    return render(request, 'strategy.html', context)

def new_result(request):
    pass

def new_comment(request):
    pass