from django.shortcuts import render

from .models import *

# Create your views here.

def get_strategies(request):
    strategies = Strategy.objects.all()
    return render(request, 'index.html', {'strategies': strategies})

def get_strategy(request, id):
    strategy = {}
    # strategy = Strategy.objects.get(id=strategy_id)
    return render(request, 'strategy.html', {'strategy': strategy})