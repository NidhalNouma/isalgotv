
from automate.models import TradeDetails
from django.contrib.contenttypes.models import ContentType

from performance.models import (
    StrategyPerformance, AccountPerformance, AssetPerformance,
    DayAssetPerformance, DayStrategyPerformance, AssetStrategyPerformance
)
from performance.functions.performance import *


def get_strategy_performance_context(strategy, perf_id):
    """Get strategy performance context within a specific account"""
    strategy_performances = StrategyPerformance.objects.filter(strategy=strategy, account_performance__id=perf_id).first()

    if not strategy_performances:
        return None

    account = strategy_performances.account_performance.account

    overview_performance = get_overview_performance_data(strategy_performances)
    chart_performance = get_strategy_day_performance(strategy_performances)
    currencies_performance = get_performance_currencies(strategy_performances)
    asset_performance = get_strategy_asset_data(strategy_performances)
    trades = TradeDetails.objects.filter(
        strategy=strategy,
        content_type=strategy_performances.account_performance.content_type,
        object_id=strategy_performances.account_performance.object_id,
        status__in=['C']
    ).order_by('-exit_time')

    return {
        'account': account,
        'overview_data': overview_performance,
        'chart_data': chart_performance,
        'currencies_performance': currencies_performance,
        'assets': asset_performance,
        'trades': trades,
        # 'next_start': trades.count(),
        'only_closed_trades': True,
    }


def get_asset_performance_context(asset, perf_id):
    """Get asset performance context within a specific account"""
    asset_performances = AssetPerformance.objects.filter(asset=asset, account_performance__id=perf_id).first()

    if not asset_performances:
        return None

    account = asset_performances.account_performance.account

    overview_performance = get_overview_performance_data(asset_performances)
    chart_performance = get_asset_day_performance(asset_performances)
    currencies_performance = get_performance_currencies(asset_performances)
    strategies = get_asset_strategy_data(asset_performances)
    trades = TradeDetails.objects.filter(
        symbol=asset,
        content_type=asset_performances.account_performance.content_type,
        object_id=asset_performances.account_performance.object_id,
        status__in=['C']
    ).order_by('-exit_time')

    return {
        'account': account,
        'overview_data': overview_performance,
        'chart_data': chart_performance,
        'currencies_performance': currencies_performance,
        'strategies': strategies,
        'trades': trades,
        # 'next_start': trades.count(),
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
    strategies = get_strategy_performance_data(account_perf)

        
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
        'perf_id': account_perf.id,
        'overview_data': overview_data,
        'chart_data': chart_performance,
        'currencies_performance': currencies_performance,
        'assets': assets,
        'strategies': strategies,
        'trades': trades,  
        'next_start': trades.count(),
        'only_closed_trades': only_closed_trades,
    }

def get_global_strategy_performance_context(strategy):
    pass