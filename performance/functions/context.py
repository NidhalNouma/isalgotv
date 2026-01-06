
from automate.models import TradeDetails
from django.contrib.contenttypes.models import ContentType

from performance.models import StrategyPerformance, AccountPerformance
from performance.functions.performance import get_performance_currencies, get_strategy_performance_data, get_days_performance, get_overview_performance_data, get_asset_performance_data, backfill_account_performance


def strategy_context_data(strategy):
    strategy_performances = StrategyPerformance.objects.filter(strategy=strategy).first()

    overview_performance = get_overview_performance_data(strategy_performances)
    chart_performance = get_days_performance(strategy_performances)
    currencies_performance = get_performance_currencies(strategy_performances)
    asset_performance = get_asset_performance_data(strategy_performances)
    trades = TradeDetails.objects.filter(
        strategy=strategy,
        status__in=['C']
    ).order_by('-exit_time')[:20]

    return {
        'overview_data': overview_performance,
        'chart_data': chart_performance,
        'currencies_performance': currencies_performance,
        'assets': asset_performance,
        'trades': trades,
        'next_start': trades.count(),
        'only_closed_trades': True,
    }

def account_context_data(account):
    ct = ContentType.objects.get_for_model(type(account))

    # Fetch AccountPerformance
    account_perf = AccountPerformance.objects.filter(content_type=ct, object_id=account.id).first()

    if not account_perf:
        account_perf = backfill_account_performance(ct, account.id, create=True)
    if not account_perf:
        return None
    
    overview_data = get_overview_performance_data(account_perf)
    chart_performance = get_days_performance(account_perf)

    currencies_performance = get_performance_currencies(account_perf)

    assets = get_asset_performance_data(account_perf)
    sources = get_strategy_performance_data(account_perf)

        
    only_closed_trades = True
    # if request.user and request.user.is_superuser:
    #     only_closed_trades = False
    # elif request.user and request.user.is_authenticated:
    #     if request.user.user_profile == account.created_by:
    #         only_closed_trades = False 
    
    trades = TradeDetails.objects.filter(
        content_type=ct,
        object_id=account.id,
        status__in=['C'] if only_closed_trades else ['O', 'P', 'C']
    ).order_by('-exit_time')[:20]

    return {
        'overview_data': overview_data,
        'chart_data': chart_performance,
        'currencies_performance': currencies_performance,
        'assets': assets,
        'sources': sources,
        'trades': trades,  
        'next_start': trades.count(),
        'only_closed_trades': only_closed_trades,
    }