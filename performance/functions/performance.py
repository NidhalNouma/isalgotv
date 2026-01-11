
from django.db import transaction
from django.db.utils import IntegrityError
from typing import TypedDict, Any, NotRequired

from performance.models import *
from automate.models import TradeDetails
import datetime

@transaction.atomic
def apply_trade_to_performance(trade):
    """
    Apply a CLOSED trade to all performance models (v2).
    Safe for retries, parallel workers, and millions of trades.
    """

    # --------------------------------------------------
    # Guards
    # --------------------------------------------------
    if trade.status != "C":
        return

    if not trade.account:
        raise ValueError("Trade has no linked account")
    
    currency = trade.currency
    if not currency or currency in ("None", None, ""):
        raise ValueError("Trade has no currency")
    
    asset = trade.symbol
    trade_date = trade.exit_time.date()
    strategy = trade.strategy

    # --------------------------------------------------
    # Resolve AccountPerformance (ONLY GFK USED)
    # --------------------------------------------------
    account_perf = AccountPerformance.objects.filter(
        content_type=trade.content_type,
        object_id=trade.object_id,
    ).first()

    if not account_perf:
        # Backfill all historical closed trades
        backfill_account_performance(trade.content_type, trade.object_id)
        return  # backfill will apply this trade too

    # --------------------------------------------------
    # Helper: apply stats ONCE
    # --------------------------------------------------
    def apply_once(perf_type, perf_id, update_fn):
        try:
            TradeAppliedPerformance.objects.create(
                trade=trade,
                performance_type=perf_type,
                performance_id=perf_id,
            )
        except IntegrityError:
            return  # already applied
        update_fn()

    # --------------------------------------------------
    # 1 AccountPerformance
    # --------------------------------------------------
    def update_account():
        AccountPerformance.apply_trade_stats(perf_id=account_perf.id, trade=trade)

    apply_once("account", account_perf.id, update_account)

    # --------------------------------------------------
    # Account Currency
    # --------------------------------------------------
    acc_curr, _ = AccountCurrencyPerformance.objects.get_or_create(
        account_performance=account_perf,
        currency=currency,
    )

    def update_account_currency():
        AccountCurrencyPerformance.apply_trade_and_profit_stats(
            perf_id=acc_curr.id,
            trade=trade,
        )

    apply_once("account_currency", acc_curr.id, update_account_currency)

    # --------------------------------------------------
    # 2 AssetPerformance
    # --------------------------------------------------
    asset_perf, _ = AssetPerformance.objects.get_or_create(
        account_performance=account_perf,
        asset=asset,
    )

    def update_asset():
        AssetPerformance.apply_trade_stats(perf_id=asset_perf.id, trade=trade)

    apply_once("asset", asset_perf.id, update_asset)

    # Asset currency
    asset_curr, _ = AssetCurrencyPerformance.objects.get_or_create(
        asset_performance=asset_perf,
        currency=currency,
    )

    def update_asset_currency():
        AssetCurrencyPerformance.apply_trade_and_profit_stats(perf_id=asset_curr.id, trade=trade)

    apply_once("asset_currency", asset_curr.id, update_asset_currency)

    # --------------------------------------------------
    # 3 StrategyPerformance (optional)
    # --------------------------------------------------
    if strategy:
        strategy_perf, _ = StrategyPerformance.objects.get_or_create(
            account_performance=account_perf,
            strategy=strategy,
        )

        def update_strategy():
            StrategyPerformance.apply_trade_stats(perf_id=strategy_perf.id, trade=trade)
        apply_once("strategy", strategy_perf.id, update_strategy)

        strategy_curr, _ = StrategyCurrencyPerformance.objects.get_or_create(
            strategy_performance=strategy_perf,
            currency=currency,
        )

        def update_strategy_currency():
            StrategyCurrencyPerformance.apply_trade_and_profit_stats(perf_id=strategy_curr.id, trade=trade)

        apply_once("strategy_currency", strategy_curr.id, update_strategy_currency)

    # --------------------------------------------------
    # 4 DayPerformance
    # --------------------------------------------------
    day_perf, _ = DayPerformance.objects.get_or_create(
        account_performance=account_perf,
        date=trade_date,
    )

    def update_day():
        DayPerformance.apply_trade_stats(perf_id=day_perf.id, trade=trade)

    apply_once("day", day_perf.id, update_day)

    # Day Currency
    day_curr, _ = DayCurrencyPerformance.objects.get_or_create(
        day_performance=day_perf,
        currency=currency,
    )

    def update_day_currency():
        DayCurrencyPerformance.apply_trade_and_profit_stats(perf_id=day_curr.id, trade=trade)

    apply_once("day_currency", day_curr.id, update_day_currency)

    # --------------------------------------------------
    # 5 DayAssetPerformance (with currency breakdown)
    # --------------------------------------------------
    day_asset_perf, _ = DayAssetPerformance.objects.get_or_create(
        day_performance=day_perf,
        asset_performance=asset_perf,
    )

    def update_day_asset():
        DayAssetPerformance.apply_trade_stats(perf_id=day_asset_perf.id, trade=trade)

    apply_once("day_asset", day_asset_perf.id, update_day_asset)

    day_asset_curr, _ = DayAssetCurrencyPerformance.objects.get_or_create(
        day_asset_performance=day_asset_perf,
        currency=currency,
    )

    def update_day_asset_currency():
        DayAssetCurrencyPerformance.apply_trade_and_profit_stats(perf_id=day_asset_curr.id, trade=trade)

    apply_once("day_asset_currency", day_asset_curr.id, update_day_asset_currency)

    # --------------------------------------------------
    # 6 DayStrategyPerformance (with currency breakdown)
    # --------------------------------------------------
    if strategy:
        day_strategy_perf, _ = DayStrategyPerformance.objects.get_or_create(
            day_performance=day_perf,
            strategy_performance=strategy_perf,
        )

        def update_day_strategy():
            DayStrategyPerformance.apply_trade_stats(perf_id=day_strategy_perf.id, trade=trade)

        apply_once("day_strategy", day_strategy_perf.id, update_day_strategy)

        day_strategy_curr, _ = DayStrategyCurrencyPerformance.objects.get_or_create(
            day_strategy_performance=day_strategy_perf,
            currency=currency,
        )

        def update_day_strategy_currency():
            DayStrategyCurrencyPerformance.apply_trade_and_profit_stats(perf_id=day_strategy_curr.id, trade=trade)

        apply_once("day_strategy_currency", day_strategy_curr.id, update_day_strategy_currency)

        # --------------------------------------------------
        # 7 AssetStrategyPerformance (strategy performance per asset)
        # --------------------------------------------------
        asset_strategy_perf, _ = AssetStrategyPerformance.objects.get_or_create(
            asset_performance=asset_perf,
            strategy_performance=strategy_perf,
        )

        def update_asset_strategy():
            AssetStrategyPerformance.apply_trade_stats(perf_id=asset_strategy_perf.id, trade=trade)

        apply_once("asset_strategy", asset_strategy_perf.id, update_asset_strategy)

        asset_strategy_curr, _ = AssetStrategyCurrencyPerformance.objects.get_or_create(
            asset_strategy_performance=asset_strategy_perf,
            currency=currency,
        )

        def update_asset_strategy_currency():
            AssetStrategyCurrencyPerformance.apply_trade_and_profit_stats(perf_id=asset_strategy_curr.id, trade=trade)

        apply_once("asset_strategy_currency", asset_strategy_curr.id, update_asset_strategy_currency)

        # --------------------------------------------------
        # 8 DayAssetStrategyPerformance (day-level asset-strategy performance)
        # --------------------------------------------------
        day_asset_strategy_perf, _ = DayAssetStrategyPerformance.objects.get_or_create(
            day_performance=day_perf,
            asset_strategy_performance=asset_strategy_perf,
        )

        def update_day_asset_strategy():
            DayAssetStrategyPerformance.apply_trade_stats(perf_id=day_asset_strategy_perf.id, trade=trade)

        apply_once("day_asset_strategy", day_asset_strategy_perf.id, update_day_asset_strategy)

        day_asset_strategy_curr, _ = DayAssetStrategyCurrencyPerformance.objects.get_or_create(
            day_asset_strategy_performance=day_asset_strategy_perf,
            currency=currency,
        )

        def update_day_asset_strategy_currency():
            DayAssetStrategyCurrencyPerformance.apply_trade_and_profit_stats(perf_id=day_asset_strategy_curr.id, trade=trade)

        apply_once("day_asset_strategy_currency", day_asset_strategy_curr.id, update_day_asset_strategy_currency)


def backfill_account_performance(content_type, object_id, create=True):
    """
    Apply ALL closed trades for this account to performance models.
    Safe to run multiple times due to TradeAppliedPerformance.
    """


    if create:
        # Create AccountPerformance
        account_perf = AccountPerformance.objects.create(
            content_type=content_type,
            object_id=object_id,
        )


    closed_trades = (
        TradeDetails.objects
        .filter(
            content_type=content_type,
            object_id=object_id,
            status="C",
        )
        .order_by("exit_time")
    )

    for t in closed_trades:
        apply_trade_to_performance(t)

    account_perf = AccountPerformance.objects.filter(
        content_type=content_type,
        object_id=object_id,
    ).first()
    return account_perf


def d(val):
    """Safe Decimal → float converter"""
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


class OverviewPerformanceData(TypedDict):
    trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    buy_trades: int
    buy_winning_trades: int
    buy_losing_trades: int
    buy_win_rate: float
    sell_trades: int
    sell_winning_trades: int
    sell_losing_trades: int
    sell_win_rate: float

def get_overview_performance_data(performance) -> OverviewPerformanceData:
    """
    Get overview performance data for this account_performance.
    """

    if not performance:
        return OverviewPerformanceData(
            trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            buy_trades=0,
            buy_winning_trades=0,
            buy_losing_trades=0,
            buy_win_rate=0.0,
            sell_trades=0,
            sell_winning_trades=0,
            sell_losing_trades=0,
            sell_win_rate=0.0,
        )

    data: OverviewPerformanceData = OverviewPerformanceData(
        trades=performance.total_trades,
        winning_trades=performance.winning_trades,  
        losing_trades=performance.losing_trades,
        win_rate=round((performance.winning_trades / performance.total_trades * 100) if performance.total_trades > 0 else 0.0, 2),
        buy_trades=performance.buy_total_trades,
        buy_winning_trades=performance.buy_winning_trades,
        buy_losing_trades=performance.buy_losing_trades,
        buy_win_rate=round((performance.buy_winning_trades / performance.buy_total_trades * 100) if performance.buy_total_trades > 0 else 0.0, 2),
        sell_trades=performance.sell_total_trades,
        sell_winning_trades=performance.sell_winning_trades,
        sell_losing_trades=performance.sell_losing_trades,
        sell_win_rate=round((performance.sell_winning_trades / performance.sell_total_trades * 100) if performance.sell_total_trades > 0 else 0.0, 2),
    )

    return data


class PerformanceData(TypedDict):
    profit: float = 0.0
    buy_profit: float = 0.0
    sell_profit: float = 0.0
    fees: float = 0.0
    buy_fees: float = 0.0
    sell_fees: float = 0.0
    net_profit: float = 0.0
    buy_net_profit: float = 0.0
    sell_net_profit: float = 0.0
    trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    buy_trades: int = 0
    buy_winning_trades: int = 0
    buy_losing_trades: int = 0
    sell_trades: int = 0
    sell_winning_trades: int = 0
    sell_losing_trades: int = 0

    profit_factor: NotRequired[float]
    buy_profit_factor: NotRequired[float]
    sell_profit_factor: NotRequired[float]

    gross_profit: NotRequired[float]
    buy_gross_profit: NotRequired[float]
    sell_gross_profit: NotRequired[float]
    gross_loss: NotRequired[float]
    buy_gross_loss: NotRequired[float]
    sell_gross_loss: NotRequired[float]

    largest_profit: NotRequired[float]
    largest_loss: NotRequired[float]
    buy_largest_profit: NotRequired[float]
    buy_largest_loss: NotRequired[float]
    sell_largest_profit: NotRequired[float]
    sell_largest_loss: NotRequired[float]

def empty_performance_data() -> PerformanceData:
    return PerformanceData(
        profit=0.0,
        buy_profit=0.0,
        sell_profit=0.0,
        fees=0.0,
        buy_fees=0.0,
        sell_fees=0.0,
        net_profit=0.0,
        buy_net_profit=0.0,
        sell_net_profit=0.0,
        trades=0,
        winning_trades=0,
        losing_trades=0,
        buy_trades=0,
        buy_winning_trades=0,
        buy_losing_trades=0,
        sell_trades=0,
        sell_winning_trades=0,
        sell_losing_trades=0,
    )

def get_performance_currencies(performance):
    """
    Get performance data for this account_performance.
    """

    if not performance:
        return empty_performance_data()

    data = {}

    for curr in performance.currencies.all():
        data[curr.currency] = PerformanceData(
            profit=d(curr.total_profit),
            buy_profit=d(curr.buy_profit),
            sell_profit=d(curr.sell_profit),
            fees=d(curr.total_fees),
            buy_fees=d(curr.buy_fees),
            sell_fees=d(curr.sell_fees),
            net_profit=d(curr.net_profit),
            buy_net_profit=d(curr.buy_net_profit),
            sell_net_profit=d(curr.sell_net_profit),
            trades=curr.total_trades,
            winning_trades=curr.winning_trades,
            losing_trades=curr.losing_trades,
            buy_trades=curr.buy_total_trades,
            buy_winning_trades=curr.buy_winning_trades,
            buy_losing_trades=curr.buy_losing_trades,
            sell_trades=curr.sell_total_trades,
            sell_winning_trades=curr.sell_winning_trades,
            sell_losing_trades=curr.sell_losing_trades,

            profit_factor=curr.profit_factor,
            buy_profit_factor=curr.buy_profit_factor,
            sell_profit_factor=curr.sell_profit_factor,

            gross_profit=curr.winning_net_profit,
            buy_gross_profit=curr.buy_winning_net_profit,
            sell_gross_profit=curr.sell_winning_net_profit,
            gross_loss=curr.losing_net_profit,
            buy_gross_loss=curr.buy_losing_net_profit,
            sell_gross_loss=curr.sell_losing_net_profit,

            largest_profit=curr.largest_net_profit,
            largest_loss=curr.largest_net_loss,
            buy_largest_profit=curr.largest_buy_net_profit,
            buy_largest_loss=curr.largest_buy_net_loss,
            sell_largest_profit=curr.largest_sell_net_profit,
            sell_largest_loss=curr.largest_sell_net_loss,
        )

    return data
class DayPerformanceData(TypedDict):
    date: str

    total_profit: float
    total_trades: int

    today_profit: float
    today_trades: int

    max_profit: float
    max_drawdown: float

class ChartDayPerformance(TypedDict):
    date: str
    data: list[DayPerformanceData]
    cumulative: PerformanceData
    max_net_profit: float
    max_drawdown: float
    today_net_profit: float
    number_of_days: int
    avg_daily_net_profit: NotRequired[float]
    avg_daily_trades: NotRequired[float]
    

def get_days_performance(performance):
    """
    Get all DayPerformance for this account_performance.
    """

    if not performance:
        return {}

    start_day = datetime.date.today()
    end_day = datetime.date(1970, 1, 1)

    per = performance.day_performances.prefetch_related('currencies').all()

    day_perf_per_currency = {}

    if performance:
        for day_perf in per:
            if day_perf.date < start_day:
                start_day = day_perf.date
            if day_perf.date > end_day:
                end_day = day_perf.date

            for curr in day_perf.currencies.all():
                day_perf_per_currency[curr.currency] = day_perf_per_currency.get(curr.currency, {})
                prev_data = day_perf_per_currency[curr.currency].get(day_perf.date, empty_performance_data())
                day_perf_per_currency[curr.currency][day_perf.date] = PerformanceData(
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


    start_day = start_day - datetime.timedelta(days=1)
    days = (end_day - start_day).days + 1
    if days < 3:
        start_day = end_day - datetime.timedelta(days=2)
        days = 3
    days_difference = [start_day + datetime.timedelta(days=i) for i in range(days)]

    chart_data = {}

    for currency, perf_data in day_perf_per_currency.items():
        chart_data[currency] = ChartDayPerformance(
            data=[],
            cumulative=empty_performance_data(),
            max_net_profit=0,
            max_drawdown=0,
        )
        number_of_days = 0
        avg_daily_net_profit = 0.0
        avg_daily_trades = 0.0

        cumulative_data = empty_performance_data()
        day_data: list[DayPerformanceData] = []
        for day in days_difference:
            daily_data = perf_data.get(day, empty_performance_data())

            for key in daily_data.keys():
                cumulative_data[key] = cumulative_data.get(key, 0) + daily_data.get(key, 0)

            max_net_profit = max(chart_data[currency]['max_net_profit'], cumulative_data.get('net_profit', 0))
            max_drawdown = min(chart_data[currency]['max_drawdown'], cumulative_data.get('net_profit', 0))
            chart_data[currency]['max_net_profit'] = max_net_profit
            chart_data[currency]['max_drawdown'] = max_drawdown 

            day_data.append(DayPerformanceData(
                date=day.strftime('%b %d, %Y'),

                today_trades=daily_data.get('trades', 0),
                today_net_profit=daily_data.get('net_profit', 0),
                total_trades=cumulative_data.get('trades', 0),
                total_net_profit=cumulative_data.get('net_profit', 0),

                max_net_profit=max_net_profit,
                max_drawdown=max_drawdown,
            ))

            if daily_data.get('trades', 0) > 0:
                number_of_days += 1
                avg_daily_net_profit += daily_data.get('net_profit', 0)
                avg_daily_trades += daily_data.get('trades', 0)

        
        today_date = datetime.date.today()
        chart_data[currency]['today_profit'] = perf_data.get(today_date, {}).get('net_profit', 0)
        chart_data[currency]['data'] = day_data
        chart_data[currency]['cumulative'] = cumulative_data

        chart_data[currency]['number_of_days'] = number_of_days
        chart_data[currency]['avg_daily_net_profit'] = (avg_daily_net_profit / number_of_days) if number_of_days > 0 else 0.0
        chart_data[currency]['avg_daily_trades'] = (avg_daily_trades / number_of_days) if number_of_days > 0 else 0.0


    return chart_data
    
class ASPerformanceData(TypedDict):
    id: NotRequired[int]
    trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    buy_trades: int = 0
    buy_winning_trades: int = 0
    buy_losing_trades: int = 0
    buy_win_rate: float = 0.0
    sell_trades: int = 0
    sell_winning_trades: int = 0
    sell_losing_trades: int = 0
    sell_win_rate: float = 0.0

    class ProfitData(TypedDict):
        profit: float = 0.0
        buy_profit: float = 0.0
        sell_profit: float = 0.0
        fees: float = 0.0
        buy_fees: float = 0.0
        sell_fees: float = 0.0
        net_profit: float = 0.0
        buy_net_profit: float = 0.0
        sell_net_profit: float = 0.0

    profit: dict[str, ProfitData] = {}

def get_asset_performance_data(performance) -> ASPerformanceData:
    """
    Get asset performance data for this account_performance.
    """
    if not performance:
        return {}
    
    data = {}

    for asset_perf in performance.asset_performances.prefetch_related('currencies').all():
        profit_dic = {c.currency: {
            "profit": d(c.total_profit),
            "buy_profit": d(c.buy_profit),
            "sell_profit": d(c.sell_profit),
            "fees": d(c.total_fees),
            "buy_fees": d(c.buy_fees),
            "sell_fees": d(c.sell_fees),
            "net_profit": d(c.net_profit),
            "buy_net_profit": d(c.buy_net_profit),
            "sell_net_profit": d(c.sell_net_profit),
        } for c in asset_perf.currencies.all()}

        data[asset_perf.asset] = ASPerformanceData(
            id=asset_perf.id,
            trades=asset_perf.total_trades,
            winning_trades=asset_perf.winning_trades,  
            losing_trades=asset_perf.losing_trades,
            win_rate=round((asset_perf.winning_trades / asset_perf.total_trades * 100) if asset_perf.total_trades > 0 else 0.0, 2),
            buy_trades=asset_perf.buy_total_trades,
            buy_winning_trades=asset_perf.buy_winning_trades,
            buy_losing_trades=asset_perf.buy_losing_trades,
            buy_win_rate=round((asset_perf.buy_winning_trades / asset_perf.buy_total_trades * 100) if asset_perf.buy_total_trades > 0 else 0.0, 2),
            sell_trades=asset_perf.sell_total_trades,
            sell_winning_trades=asset_perf.sell_winning_trades,
            sell_losing_trades=asset_perf.sell_losing_trades,
            sell_win_rate=round((asset_perf.sell_winning_trades / asset_perf.sell_total_trades * 100) if asset_perf.sell_total_trades > 0 else 0.0, 2),
            profit=profit_dic
        )
    return data

def get_strategy_performance_data(performance) -> ASPerformanceData:
    """
    Get strategy performance data for this account_performance.
    """
    if not performance:
        return {}
    
    data = {}

    for strategy_perf in performance.strategy_performances.prefetch_related('currencies', 'strategy').all():
        profit_dic = {c.currency: {
            "profit": d(c.total_profit),
            "buy_profit": d(c.buy_profit),
            "sell_profit": d(c.sell_profit),
            "fees": d(c.total_fees),
            "buy_fees": d(c.buy_fees),
            "sell_fees": d(c.sell_fees),
            "net_profit": d(c.net_profit),
            "buy_net_profit": d(c.buy_net_profit),
            "sell_net_profit": d(c.sell_net_profit),
        } for c in strategy_perf.currencies.all()}

        data[strategy_perf.strategy] = ASPerformanceData(
            id=strategy_perf.id,
            trades=strategy_perf.total_trades,
            winning_trades=strategy_perf.winning_trades,  
            losing_trades=strategy_perf.losing_trades,
            win_rate=round((strategy_perf.winning_trades / strategy_perf.total_trades * 100) if strategy_perf.total_trades > 0 else 0.0, 2),
            buy_trades=strategy_perf.buy_total_trades,
            buy_winning_trades=strategy_perf.buy_winning_trades,
            buy_losing_trades=strategy_perf.buy_losing_trades,
            buy_win_rate=round((strategy_perf.buy_winning_trades / strategy_perf.buy_total_trades * 100) if strategy_perf.buy_total_trades > 0 else 0.0, 2),
            sell_trades=strategy_perf.sell_total_trades,
            sell_winning_trades=strategy_perf.sell_winning_trades,
            sell_losing_trades=strategy_perf.sell_losing_trades,
            sell_win_rate=round((strategy_perf.sell_winning_trades / strategy_perf.sell_total_trades * 100) if strategy_perf.sell_total_trades > 0 else 0.0, 2),
            profit=profit_dic
        )
    return data


def get_asset_day_performance(asset_performance):
    """
    Get day-by-day performance for a specific asset (within an account).
    Uses DayAssetPerformance and DayAssetCurrencyPerformance.
    """
    if not asset_performance:
        return {}

    start_day = datetime.date.today()
    end_day = datetime.date(1970, 1, 1)

    day_asset_perfs = DayAssetPerformance.objects.filter(
        asset_performance=asset_performance
    ).select_related('day_performance').prefetch_related('currencies')

    day_perf_per_currency = {}

    for day_asset_perf in day_asset_perfs:
        trade_date = day_asset_perf.day_performance.date
        if trade_date < start_day:
            start_day = trade_date
        if trade_date > end_day:
            end_day = trade_date

        for curr in day_asset_perf.currencies.all():
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

    return _build_chart_data(day_perf_per_currency, start_day, end_day)


def get_strategy_day_performance(strategy_performance):
    """
    Get day-by-day performance for a specific strategy (within an account).
    Uses DayStrategyPerformance and DayStrategyCurrencyPerformance.
    """
    if not strategy_performance:
        return {}

    start_day = datetime.date.today()
    end_day = datetime.date(1970, 1, 1)

    day_strategy_perfs = DayStrategyPerformance.objects.filter(
        strategy_performance=strategy_performance
    ).select_related('day_performance').prefetch_related('currencies')

    day_perf_per_currency = {}

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

    return _build_chart_data(day_perf_per_currency, start_day, end_day)


def get_asset_strategy_day_performance(asset_strategy_performance):
    """
    Get day-by-day performance for a specific asset-strategy combination.
    Uses DayAssetStrategyPerformance and DayAssetStrategyCurrencyPerformance.
    """
    if not asset_strategy_performance:
        return {}

    start_day = datetime.date.today()
    end_day = datetime.date(1970, 1, 1)

    day_asset_strategy_perfs = DayAssetStrategyPerformance.objects.filter(
        asset_strategy_performance=asset_strategy_performance
    ).select_related('day_performance').prefetch_related('currencies')

    day_perf_per_currency = {}

    for day_asset_strategy_perf in day_asset_strategy_perfs:
        trade_date = day_asset_strategy_perf.day_performance.date
        if trade_date < start_day:
            start_day = trade_date
        if trade_date > end_day:
            end_day = trade_date

        for curr in day_asset_strategy_perf.currencies.all():
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

    return _build_chart_data(day_perf_per_currency, start_day, end_day)


def _build_chart_data(day_perf_per_currency, start_day, end_day):
    """Helper function to build chart data from day performance per currency."""
    if not day_perf_per_currency:
        return {}

    start_day = start_day - datetime.timedelta(days=1)
    days = (end_day - start_day).days + 1
    if days < 3:
        start_day = end_day - datetime.timedelta(days=2)
        days = 3
    days_difference = [start_day + datetime.timedelta(days=i) for i in range(days)]

    chart_data = {}

    for currency, perf_data in day_perf_per_currency.items():
        chart_data[currency] = ChartDayPerformance(
            data=[],
            cumulative=empty_performance_data(),
            max_net_profit=0,
            max_drawdown=0,
        )
        number_of_days = 0
        avg_daily_net_profit = 0.0
        avg_daily_trades = 0.0

        cumulative_data = empty_performance_data()
        day_data: list[DayPerformanceData] = []
        for day in days_difference:
            daily_data = perf_data.get(day, empty_performance_data())

            for key in daily_data.keys():
                cumulative_data[key] = cumulative_data.get(key, 0) + daily_data.get(key, 0)

            max_net_profit = max(chart_data[currency]['max_net_profit'], cumulative_data.get('net_profit', 0))
            max_drawdown = min(chart_data[currency]['max_drawdown'], cumulative_data.get('net_profit', 0))
            chart_data[currency]['max_net_profit'] = max_net_profit
            chart_data[currency]['max_drawdown'] = max_drawdown 

            day_data.append(DayPerformanceData(
                date=day.strftime('%b %d, %Y'),
                today_trades=daily_data.get('trades', 0),
                today_net_profit=daily_data.get('net_profit', 0),
                total_trades=cumulative_data.get('trades', 0),
                total_net_profit=cumulative_data.get('net_profit', 0),
                max_net_profit=max_net_profit,
                max_drawdown=max_drawdown,
            ))

            if daily_data.get('trades', 0) > 0:
                number_of_days += 1
                avg_daily_net_profit += daily_data.get('net_profit', 0)
                avg_daily_trades += daily_data.get('trades', 0)

        today_date = datetime.date.today()
        chart_data[currency]['today_profit'] = perf_data.get(today_date, {}).get('net_profit', 0)
        chart_data[currency]['data'] = day_data
        chart_data[currency]['cumulative'] = cumulative_data

        chart_data[currency]['number_of_days'] = number_of_days
        chart_data[currency]['avg_daily_net_profit'] = (avg_daily_net_profit / number_of_days) if number_of_days > 0 else 0.0
        chart_data[currency]['avg_daily_trades'] = (avg_daily_trades / number_of_days) if number_of_days > 0 else 0.0

    return chart_data


def get_asset_strategy_data(asset_performance) -> ASPerformanceData:
    """
    Get strategies that traded this asset (within the same account).
    Uses AssetStrategyPerformance.
    """
    if not asset_performance:
        return {}
    
    data = {}

    for asset_strategy_perf in AssetStrategyPerformance.objects.filter(
        asset_performance=asset_performance
    ).select_related('strategy_performance__strategy').prefetch_related('currencies'):
        
        strategy = asset_strategy_perf.strategy_performance.strategy
        
        profit_dic = {c.currency: {
            "profit": d(c.total_profit),
            "buy_profit": d(c.buy_profit),
            "sell_profit": d(c.sell_profit),
            "fees": d(c.total_fees),
            "buy_fees": d(c.buy_fees),
            "sell_fees": d(c.sell_fees),
            "net_profit": d(c.net_profit),
            "buy_net_profit": d(c.buy_net_profit),
            "sell_net_profit": d(c.sell_net_profit),
        } for c in asset_strategy_perf.currencies.all()}

        data[strategy] = ASPerformanceData(
            id=asset_strategy_perf.strategy_performance.id,
            trades=asset_strategy_perf.total_trades,
            winning_trades=asset_strategy_perf.winning_trades,  
            losing_trades=asset_strategy_perf.losing_trades,
            win_rate=round((asset_strategy_perf.winning_trades / asset_strategy_perf.total_trades * 100) if asset_strategy_perf.total_trades > 0 else 0.0, 2),
            buy_trades=asset_strategy_perf.buy_total_trades,
            buy_winning_trades=asset_strategy_perf.buy_winning_trades,
            buy_losing_trades=asset_strategy_perf.buy_losing_trades,
            buy_win_rate=round((asset_strategy_perf.buy_winning_trades / asset_strategy_perf.buy_total_trades * 100) if asset_strategy_perf.buy_total_trades > 0 else 0.0, 2),
            sell_trades=asset_strategy_perf.sell_total_trades,
            sell_winning_trades=asset_strategy_perf.sell_winning_trades,
            sell_losing_trades=asset_strategy_perf.sell_losing_trades,
            sell_win_rate=round((asset_strategy_perf.sell_winning_trades / asset_strategy_perf.sell_total_trades * 100) if asset_strategy_perf.sell_total_trades > 0 else 0.0, 2),
            profit=profit_dic
        )
    return data


def get_strategy_asset_data(strategy_performance) -> ASPerformanceData:
    """
    Get assets traded by this strategy (within the same account).
    Uses AssetStrategyPerformance.
    """
    if not strategy_performance:
        return {}
    
    data = {}

    for asset_strategy_perf in AssetStrategyPerformance.objects.filter(
        strategy_performance=strategy_performance
    ).select_related('asset_performance').prefetch_related('currencies'):
        
        asset = asset_strategy_perf.asset_performance.asset
        
        profit_dic = {c.currency: {
            "profit": d(c.total_profit),
            "buy_profit": d(c.buy_profit),
            "sell_profit": d(c.sell_profit),
            "fees": d(c.total_fees),
            "buy_fees": d(c.buy_fees),
            "sell_fees": d(c.sell_fees),
            "net_profit": d(c.net_profit),
            "buy_net_profit": d(c.buy_net_profit),
            "sell_net_profit": d(c.sell_net_profit),
        } for c in asset_strategy_perf.currencies.all()}

        data[asset] = ASPerformanceData(
            id=asset_strategy_perf.asset_performance.id,
            trades=asset_strategy_perf.total_trades,
            winning_trades=asset_strategy_perf.winning_trades,  
            losing_trades=asset_strategy_perf.losing_trades,
            win_rate=round((asset_strategy_perf.winning_trades / asset_strategy_perf.total_trades * 100) if asset_strategy_perf.total_trades > 0 else 0.0, 2),
            buy_trades=asset_strategy_perf.buy_total_trades,
            buy_winning_trades=asset_strategy_perf.buy_winning_trades,
            buy_losing_trades=asset_strategy_perf.buy_losing_trades,
            buy_win_rate=round((asset_strategy_perf.buy_winning_trades / asset_strategy_perf.buy_total_trades * 100) if asset_strategy_perf.buy_total_trades > 0 else 0.0, 2),
            sell_trades=asset_strategy_perf.sell_total_trades,
            sell_winning_trades=asset_strategy_perf.sell_winning_trades,
            sell_losing_trades=asset_strategy_perf.sell_losing_trades,
            sell_win_rate=round((asset_strategy_perf.sell_winning_trades / asset_strategy_perf.sell_total_trades * 100) if asset_strategy_perf.sell_total_trades > 0 else 0.0, 2),
            profit=profit_dic
        )
    return data