
from automate.models import TradeDetails
from django.contrib.contenttypes.models import ContentType

from performance.models import (
    StrategyPerformance, AccountPerformance, AssetPerformance,
    AssetStrategyPerformance
)
from performance.functions.performance import *
from performance.functions.performance import _build_chart_data


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
    ).order_by('-exit_time')[:20]

    return {
        'cid': f'strategy-{account.id}-{strategy_performances.id}',
        'perf_id': strategy_performances.account_performance.id,
        'strategy_perf_id': strategy_performances.id,
        'account': account,
        'strategy': strategy_performances.strategy,
        'overview_data': overview_performance,
        'chart_data': chart_performance,
        'currencies_performance': currencies_performance,
        'assets': asset_performance,
        'trades': trades,
        'trades_broker_type': f"strategy-{strategy_performances.account_performance.content_type.model}-{strategy_performances.account_performance.object_id}",
        'trades_id': strategy,
        'next_start': trades.count(),
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
    ).order_by('-exit_time')[:20]

    return {
        'cid': f'asset-{account.id}-{asset_performances.id}',
        'perf_id': asset_performances.account_performance.id,
        'asset_perf_id': asset_performances.id,
        'asset': asset,
        'account': account,
        'overview_data': overview_performance,
        'chart_data': chart_performance,
        'currencies_performance': currencies_performance,
        'strategies': strategies,
        'trades': trades,
        'trades_broker_type': f"asset-{asset_performances.account_performance.content_type.model}-{asset_performances.account_performance.object_id}",
        'trades_id': asset,
        'next_start': trades.count(),
        'only_closed_trades': True,
    }

def get_strategy_asset_performance_context(strategy_perf_id, asset_perf_id):
    """Get strategy performance for a specific asset within a specific account"""
    asset_strategy_performances = AssetStrategyPerformance.objects.filter(
        strategy_performance__id=strategy_perf_id,
        asset_performance__id=asset_perf_id
    ).first()

    if not asset_strategy_performances:
        return None

    account = asset_strategy_performances.strategy_performance.account_performance.account
    
    # Extract actual strategy and asset from the performance objects
    strategy = asset_strategy_performances.strategy_performance.strategy
    asset = asset_strategy_performances.asset_performance.asset

    overview_performance = get_overview_performance_data(asset_strategy_performances)
    chart_performance = get_asset_strategy_day_performance(asset_strategy_performances)
    currencies_performance = get_performance_currencies(asset_strategy_performances)

    trades = TradeDetails.objects.filter(
        symbol=asset,
        strategy=strategy,
        content_type=asset_strategy_performances.strategy_performance.account_performance.content_type,
        object_id=asset_strategy_performances.strategy_performance.account_performance.object_id,
        status__in=['C']
    ).order_by('-exit_time')[:20]

    return {
        'cid': f'asset-strategy-{account.id}-{asset_strategy_performances.id}',
        'perf_id': asset_strategy_performances.strategy_performance.account_performance.id,
        'account': account,
        'asset': asset,
        'strategy': strategy,
        'overview_data': overview_performance,
        'chart_data': chart_performance,
        'currencies_performance': currencies_performance,
        'trades': trades,
        'trades_broker_type': f"assetNstrategy-{asset}-{asset_strategy_performances.strategy_performance.account_performance.content_type.model}-{asset_strategy_performances.strategy_performance.account_performance.object_id}",
        'trades_id': f"{strategy.id}",
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

    if overview_data.get('trades', 0) == 0:
        return {
            'perf_emsg': 'No data available at this time.',
        }

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
        'cid': f'account-{account_perf.id}',
        'perf_id': account_perf.id,
        'overview_data': overview_data,
        'chart_data': chart_performance,
        'currencies_performance': currencies_performance,
        'assets': assets,
        'strategies': strategies,
        'trades': trades,  
        'next_start': trades.count(),
        'trades_broker_type': f"{account.broker_type}",
        'trades_id': account.id,
        'only_closed_trades': only_closed_trades,
    }

def get_global_strategy_performance_context(strategy):
    """
    Get aggregated performance context for a strategy across ALL accounts.
    Returns data in the same shape as account_context_data so templates can reuse.
    """

    strategy_perfs = StrategyPerformance.objects.filter(strategy=strategy)

    if not strategy_perfs.exists():
        return {'show_performance': False}

    # ── Aggregate overview stats across all accounts ──
    total_buy_total = 0
    total_buy_winning = 0
    total_buy_losing = 0
    total_sell_total = 0
    total_sell_winning = 0
    total_sell_losing = 0

    for sp in strategy_perfs:
        total_buy_total += sp.buy_total_trades
        total_buy_winning += sp.buy_winning_trades
        total_buy_losing += sp.buy_losing_trades
        total_sell_total += sp.sell_total_trades
        total_sell_winning += sp.sell_winning_trades
        total_sell_losing += sp.sell_losing_trades

    total_trades = total_buy_total + total_sell_total
    winning_trades = total_buy_winning + total_sell_winning
    losing_trades = total_buy_losing + total_sell_losing

    if total_trades == 0:
        return {'show_performance': False}

    overview_data = {
        'trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': round((winning_trades / total_trades * 100) if total_trades > 0 else 0.0, 2),
        'buy_trades': total_buy_total,
        'buy_winning_trades': total_buy_winning,
        'buy_losing_trades': total_buy_losing,
        'buy_win_rate': round((total_buy_winning / total_buy_total * 100) if total_buy_total > 0 else 0.0, 2),
        'sell_trades': total_sell_total,
        'sell_winning_trades': total_sell_winning,
        'sell_losing_trades': total_sell_losing,
        'sell_win_rate': round((total_sell_winning / total_sell_total * 100) if total_sell_total > 0 else 0.0, 2),
    }

    # ── Aggregate currency performance across all accounts ──
    currencies_data = {}
    for curr in StrategyCurrencyPerformance.objects.filter(strategy_performance__in=strategy_perfs):
        key = curr.currency
        if key not in currencies_data:
            currencies_data[key] = empty_performance_data()

        prev = currencies_data[key]
        currencies_data[key] = PerformanceData(
            profit=d(curr.total_profit) + prev['profit'],
            buy_profit=d(curr.buy_profit) + prev['buy_profit'],
            sell_profit=d(curr.sell_profit) + prev['sell_profit'],
            fees=d(curr.total_fees) + prev['fees'],
            buy_fees=d(curr.buy_fees) + prev['buy_fees'],
            sell_fees=d(curr.sell_fees) + prev['sell_fees'],
            net_profit=d(curr.net_profit) + prev['net_profit'],
            buy_net_profit=d(curr.buy_net_profit) + prev['buy_net_profit'],
            sell_net_profit=d(curr.sell_net_profit) + prev['sell_net_profit'],
            trades=curr.total_trades + prev['trades'],
            winning_trades=curr.winning_trades + prev['winning_trades'],
            losing_trades=curr.losing_trades + prev['losing_trades'],
            buy_trades=curr.buy_total_trades + prev['buy_trades'],
            buy_winning_trades=curr.buy_winning_trades + prev['buy_winning_trades'],
            buy_losing_trades=curr.buy_losing_trades + prev['buy_losing_trades'],
            sell_trades=curr.sell_total_trades + prev['sell_trades'],
            sell_winning_trades=curr.sell_winning_trades + prev['sell_winning_trades'],
            sell_losing_trades=curr.sell_losing_trades + prev['sell_losing_trades'],
            gross_net_profit=d(curr.winning_net_profit) + prev.get('gross_net_profit', 0),
            buy_gross_net_profit=d(curr.buy_winning_net_profit) + prev.get('buy_gross_net_profit', 0),
            sell_gross_net_profit=d(curr.sell_winning_net_profit) + prev.get('sell_gross_net_profit', 0),
            gross_net_loss=d(curr.losing_net_profit) + prev.get('gross_net_loss', 0),
            buy_gross_net_loss=d(curr.buy_losing_net_profit) + prev.get('buy_gross_net_loss', 0),
            sell_gross_net_loss=d(curr.sell_losing_net_profit) + prev.get('sell_gross_net_loss', 0),
            gross_profit=d(curr.winning_profit) + prev.get('gross_profit', 0),
            buy_gross_profit=d(curr.buy_winning_profit) + prev.get('buy_gross_profit', 0),
            sell_gross_profit=d(curr.sell_winning_profit) + prev.get('sell_gross_profit', 0),
            gross_loss=d(curr.losing_profit) + prev.get('gross_loss', 0),
            buy_gross_loss=d(curr.buy_losing_profit) + prev.get('buy_gross_loss', 0),
            sell_gross_loss=d(curr.sell_losing_profit) + prev.get('sell_gross_loss', 0),
            largest_profit=max(d(curr.largest_net_profit), prev.get('largest_profit', 0)),
            largest_loss=min(d(curr.largest_net_loss), prev.get('largest_loss', 0)),
            buy_largest_profit=max(d(curr.largest_buy_net_profit), prev.get('buy_largest_profit', 0)),
            buy_largest_loss=min(d(curr.largest_buy_net_loss), prev.get('buy_largest_loss', 0)),
            sell_largest_profit=max(d(curr.largest_sell_net_profit), prev.get('sell_largest_profit', 0)),
            sell_largest_loss=min(d(curr.largest_sell_net_loss), prev.get('sell_largest_loss', 0)),
        )

    # Compute profit factors after aggregation
    for key, cd in currencies_data.items():
        gross_win = cd.get('gross_net_profit', 0)
        gross_loss_val = cd.get('gross_net_loss', 0)
        buy_gross_win = cd.get('buy_gross_net_profit', 0)
        buy_gross_loss_val = cd.get('buy_gross_net_loss', 0)
        sell_gross_win = cd.get('sell_gross_net_profit', 0)
        sell_gross_loss_val = cd.get('sell_gross_net_loss', 0)
        cd['profit_factor'] = (gross_win / abs(gross_loss_val)) if gross_loss_val != 0 else 0
        cd['buy_profit_factor'] = (buy_gross_win / abs(buy_gross_loss_val)) if buy_gross_loss_val != 0 else 0
        cd['sell_profit_factor'] = (sell_gross_win / abs(sell_gross_loss_val)) if sell_gross_loss_val != 0 else 0

    # ── Aggregate day-by-day chart data across all accounts ──
    import datetime

    start_day = datetime.date.today()
    end_day = datetime.date(1970, 1, 1)
    day_perf_per_currency = {}

    day_strategy_perfs = DayStrategyPerformance.objects.filter(
        strategy_performance__in=strategy_perfs
    ).select_related('day_performance').prefetch_related('currencies')

    for day_strategy_perf in day_strategy_perfs:
        trade_date = day_strategy_perf.day_performance.date
        if trade_date < start_day:
            start_day = trade_date
        if trade_date > end_day:
            end_day = trade_date

        for curr in day_strategy_perf.currencies.all():
            day_perf_per_currency[curr.currency] = day_perf_per_currency.get(curr.currency, {})
            prev_data = day_perf_per_currency[curr.currency].get(trade_date, empty_performance_data())
            day_perf_per_currency[curr.currency][trade_date] = PerformanceData(
                profit=d(curr.total_profit) + prev_data['profit'],
                fees=d(curr.total_fees) + prev_data['fees'],
                buy_fees=d(curr.buy_fees) + prev_data['buy_fees'],
                sell_fees=d(curr.sell_fees) + prev_data['sell_fees'],
                buy_profit=d(curr.buy_profit) + prev_data['buy_profit'],
                sell_profit=d(curr.sell_profit) + prev_data['sell_profit'],
                net_profit=d(curr.net_profit) + prev_data['net_profit'],
                buy_net_profit=d(curr.buy_net_profit) + prev_data['buy_net_profit'],
                sell_net_profit=d(curr.sell_net_profit) + prev_data['sell_net_profit'],
                trades=curr.total_trades + prev_data['trades'],
                winning_trades=curr.winning_trades + prev_data['winning_trades'],
                losing_trades=curr.losing_trades + prev_data['losing_trades'],
                buy_trades=curr.buy_total_trades + prev_data['buy_trades'],
                buy_winning_trades=curr.buy_winning_trades + prev_data['buy_winning_trades'],
                buy_losing_trades=curr.buy_losing_trades + prev_data['buy_losing_trades'],
                sell_trades=curr.sell_total_trades + prev_data['sell_trades'],
                sell_winning_trades=curr.sell_winning_trades + prev_data['sell_winning_trades'],
                sell_losing_trades=curr.sell_losing_trades + prev_data['sell_losing_trades'],
            )

    chart_data = _build_chart_data(day_perf_per_currency, start_day, end_day)

    # ── Aggregate asset performance across all accounts ──
    asset_data = {}
    for asp in AssetStrategyPerformance.objects.filter(
        strategy_performance__in=strategy_perfs
    ).select_related('asset_performance').prefetch_related('currencies'):
        asset_name = asp.asset_performance.asset

        if asset_name not in asset_data:
            asset_data[asset_name] = {
                'trades': 0, 'winning_trades': 0, 'losing_trades': 0,
                'buy_trades': 0, 'buy_winning_trades': 0, 'buy_losing_trades': 0,
                'sell_trades': 0, 'sell_winning_trades': 0, 'sell_losing_trades': 0,
                'profit': {},
            }

        a = asset_data[asset_name]
        a['trades'] += asp.total_trades
        a['winning_trades'] += asp.winning_trades
        a['losing_trades'] += asp.losing_trades
        a['buy_trades'] += asp.buy_total_trades
        a['buy_winning_trades'] += asp.buy_winning_trades
        a['buy_losing_trades'] += asp.buy_losing_trades
        a['sell_trades'] += asp.sell_total_trades
        a['sell_winning_trades'] += asp.sell_winning_trades
        a['sell_losing_trades'] += asp.sell_losing_trades

        for c in asp.currencies.all():
            if c.currency not in a['profit']:
                a['profit'][c.currency] = {
                    'profit': 0, 'buy_profit': 0, 'sell_profit': 0,
                    'fees': 0, 'buy_fees': 0, 'sell_fees': 0,
                    'net_profit': 0, 'buy_net_profit': 0, 'sell_net_profit': 0,
                }
            p = a['profit'][c.currency]
            p['profit'] += d(c.total_profit)
            p['buy_profit'] += d(c.buy_profit)
            p['sell_profit'] += d(c.sell_profit)
            p['fees'] += d(c.total_fees)
            p['buy_fees'] += d(c.buy_fees)
            p['sell_fees'] += d(c.sell_fees)
            p['net_profit'] += d(c.net_profit)
            p['buy_net_profit'] += d(c.buy_net_profit)
            p['sell_net_profit'] += d(c.sell_net_profit)

    # Convert to ASPerformanceData format
    assets = {}
    for asset_name, a in asset_data.items():
        total = a['trades']
        assets[asset_name] = ASPerformanceData(
            trades=total,
            winning_trades=a['winning_trades'],
            losing_trades=a['losing_trades'],
            win_rate=round((a['winning_trades'] / total * 100) if total > 0 else 0.0, 2),
            buy_trades=a['buy_trades'],
            buy_winning_trades=a['buy_winning_trades'],
            buy_losing_trades=a['buy_losing_trades'],
            buy_win_rate=round((a['buy_winning_trades'] / a['buy_trades'] * 100) if a['buy_trades'] > 0 else 0.0, 2),
            sell_trades=a['sell_trades'],
            sell_winning_trades=a['sell_winning_trades'],
            sell_losing_trades=a['sell_losing_trades'],
            sell_win_rate=round((a['sell_winning_trades'] / a['sell_trades'] * 100) if a['sell_trades'] > 0 else 0.0, 2),
            profit=a['profit'],
        )

    # ── Recent trades across all accounts ──
    trades = TradeDetails.objects.filter(
        strategy=strategy,
        status__in=['C']
    ).order_by('-exit_time')[:20]

    return {
        'show_performance': True,
        'cid': f'global-strategy-{strategy.id}',
        'strategy': strategy,
        'overview_data': overview_data,
        'chart_data': chart_data,
        'currencies_performance': currencies_data,
        'assets': assets,
        'trades': trades,
        'trades_broker_type': f"strategy-{strategy.id}",
        'trades_id': strategy,
        'next_start': trades.count(),
        'only_closed_trades': True,
    }