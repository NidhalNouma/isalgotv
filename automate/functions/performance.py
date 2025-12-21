
from django.db import transaction
from django.db.utils import IntegrityError

from automate.models import *

@transaction.atomic
def apply_trade_to_performance(trade: TradeDetails):
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
        AccountCurrencyPerformance.apply_trade_stats(
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
        AssetCurrencyPerformance.apply_trade_stats(perf_id=asset_curr.id, trade=trade)

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
            StrategyCurrencyPerformance.apply_trade_stats(perf_id=strategy_curr.id, trade=trade)

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

    # Link day to asset
    DayAssetPerformance.objects.get_or_create(
        day_performance=day_perf,
        asset_performance=asset_perf,
    )
    if strategy:
        DayStrategyPerformance.objects.get_or_create(
            day_performance=day_perf,
            strategy_performance=strategy_perf,
        )

    day_curr, _ = DayCurrencyPerformance.objects.get_or_create(
        day_performance=day_perf,
        currency=currency,
    )

    def update_day_currency():
        DayCurrencyPerformance.apply_trade_stats(perf_id=day_curr.id, trade=trade)

    apply_once("day_currency", day_curr.id, update_day_currency)


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