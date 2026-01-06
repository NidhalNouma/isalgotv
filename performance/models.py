
from django.db import IntegrityError, models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from django.db.models import F, Value
from django.db.models.functions import Greatest, Least

from decimal import Decimal, InvalidOperation

from strategies.models import Strategy

# analytics models ------------------------------------------------------------

# --------------------------------------------------
# TradeAppliedPerformance 
# --------------------------------------------------

class TradeAppliedPerformance(models.Model):
    trade = models.ForeignKey(
        "automate.TradeDetails",
        on_delete=models.CASCADE,
        related_name="applied_performances"
    )

    performance_type = models.CharField(max_length=32)
    performance_id = models.PositiveBigIntegerField()

    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["trade", "performance_type", "performance_id"],
                name="unique_trade_performance_application_v2"
            )
        ]
        indexes = [
            models.Index(fields=["trade"]),
            models.Index(fields=["performance_type", "performance_id"]),
        ]

    def __str__(self):
        return f"{self.trade_id} → {self.performance_type}:{self.performance_id}"


# --------------------------------------------------
# BasePerformance
# --------------------------------------------------

class BasePerformance(models.Model):
    buy_total_trades = models.PositiveIntegerField(default=0)
    buy_winning_trades = models.PositiveIntegerField(default=0)
    buy_losing_trades = models.PositiveIntegerField(default=0)

    sell_total_trades = models.PositiveIntegerField(default=0)
    sell_winning_trades = models.PositiveIntegerField(default=0)
    sell_losing_trades = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def total_trades(self):
        return self.buy_total_trades + self.sell_total_trades
    
    @property
    def winning_trades(self):
        return self.buy_winning_trades + self.sell_winning_trades
    
    @property
    def losing_trades(self):
        return self.buy_losing_trades + self.sell_losing_trades

    @property
    def win_rate(self):
        return (self.winning_trades / self.total_trades * 100) if self.total_trades else Decimal("0")

    @property
    def buy_win_rate(self):
        return (self.buy_winning_trades / self.buy_total_trades * 100) if self.buy_total_trades else Decimal("0")

    @property
    def sell_win_rate(self):
        return (self.sell_winning_trades / self.sell_total_trades * 100) if self.sell_total_trades else Decimal("0")
    
    @classmethod
    def with_totals_trades(cls):
        return cls.objects.annotate(
            total_trades=F("buy_total_trades") + F("sell_total_trades"),
            winning_trades=F("buy_winning_trades") + F("sell_winning_trades"),
            losing_trades=F("buy_losing_trades") + F("sell_losing_trades"),
        )

    @classmethod
    def apply_trade_stats(cls, perf_id, *, trade):
        """
        Atomic update of trade counters.
        """
        net_profit = trade.net_profit
        profit = trade.profit
        side = trade.side

        is_a_win = net_profit > 0
        is_a_loss = net_profit < 0

        return cls.objects.filter(id=perf_id).update(
            buy_total_trades=F("buy_total_trades") + (1 if side == "B" else 0),
            buy_winning_trades=F("buy_winning_trades") + (1 if side == "B" and is_a_win else 0),
            buy_losing_trades=F("buy_losing_trades") + (1 if side == "B" and is_a_loss else 0),

            sell_total_trades=F("sell_total_trades") + (1 if side == "S" else 0),
            sell_winning_trades=F("sell_winning_trades") + (1 if side == "S" and is_a_win else 0),
            sell_losing_trades=F("sell_losing_trades") + (1 if side == "S" and is_a_loss else 0),
        )

# --------------------------------------------------
# AccountPerformance 
# --------------------------------------------------

class AccountPerformance(BasePerformance):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="account_performances")
    object_id = models.PositiveIntegerField()
    account = GenericForeignKey("content_type", "object_id")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="unique_account_performance"
            )
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"AccountPerformance({self.content_type.model}:{self.object_id})"


# --------------------------------------------------
# AssetPerformance 
# --------------------------------------------------

class AssetPerformance(BasePerformance):
    account_performance = models.ForeignKey(
        AccountPerformance,
        on_delete=models.CASCADE,
        related_name="asset_performances"
    )

    asset = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account_performance", "asset"],
                name="unique_asset_per_account"
            )
        ]
        indexes = [
            models.Index(fields=["account_performance", "asset"]),
        ]

    def __str__(self):
        return f"{self.asset} ({self.account_performance_id})"


# --------------------------------------------------
# StrategyPerformance
# --------------------------------------------------

class StrategyPerformance(BasePerformance):
    account_performance = models.ForeignKey(
        AccountPerformance,
        on_delete=models.CASCADE,
        related_name="strategy_performances"
    )

    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account_performance", "strategy"],
                name="unique_strategy_per_account"
            )
        ]

    def __str__(self):
        return f"{self.strategy.name} ({self.account_performance_id})"
    
    @property
    def asset_performances(self):
        return AssetPerformance.objects.filter(
            day_performances__strategies=self
        ).distinct()


# --------------------------------------------------
# DayPerformance 
# --------------------------------------------------

class DayPerformance(BasePerformance):
    account_performance = models.ForeignKey(
        AccountPerformance,
        on_delete=models.CASCADE,
        related_name="day_performances"
    )

    date = models.DateField()

    assets = models.ManyToManyField(
        "AssetPerformance",
        through="DayAssetPerformance",
        related_name="day_performances"
    )

    strategies = models.ManyToManyField(
        "StrategyPerformance",
        through="DayStrategyPerformance",
        related_name="day_performances"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account_performance", "date"],
                name="unique_day_per_account"
            )
        ]
        indexes = [
            models.Index(fields=["account_performance", "date"]),
            models.Index(fields=["date"]),
        ]

class DayAssetPerformance(models.Model):
    day_performance = models.ForeignKey(
        DayPerformance,
        on_delete=models.CASCADE
    )

    asset_performance = models.ForeignKey(
        AssetPerformance,
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["day_performance", "asset_performance"],
                name="unique_asset_per_day"
            )
        ]
        indexes = [
            models.Index(fields=["day_performance"]),
            models.Index(fields=["asset_performance"]),
        ]

class DayStrategyPerformance(models.Model):
    day_performance = models.ForeignKey(
        DayPerformance,
        on_delete=models.CASCADE
    )

    strategy_performance = models.ForeignKey(
        StrategyPerformance,
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["day_performance", "strategy_performance"],
                name="unique_strategy_per_day"
            )
        ]
        indexes = [
            models.Index(fields=["day_performance"]),
            models.Index(fields=["strategy_performance"]),
        ]

# --------------------------------------------------
# Currency Performances 
# --------------------------------------------------

class CurrencyBasePerformance(BasePerformance):
    currency = models.CharField(max_length=10)

    buy_winning_net_profit = models.DecimalField(max_digits=40, decimal_places=10, default=0)
    sell_winning_net_profit = models.DecimalField(max_digits=40, decimal_places=10, default=0)

    buy_winning_fees = models.DecimalField(max_digits=40, decimal_places=10, default=0)
    sell_winning_fees = models.DecimalField(max_digits=40, decimal_places=10, default=0)

    buy_losing_net_profit = models.DecimalField(max_digits=40, decimal_places=10, default=0)
    sell_losing_net_profit = models.DecimalField(max_digits=40, decimal_places=10, default=0)

    buy_losing_fees = models.DecimalField(max_digits=40, decimal_places=10, default=0)
    sell_losing_fees = models.DecimalField(max_digits=40, decimal_places=10, default=0)

    largest_buy_net_profit = models.DecimalField(max_digits=40, decimal_places=10, default=0)
    largest_sell_net_profit = models.DecimalField(max_digits=40, decimal_places=10, default=0)
    largest_buy_net_loss = models.DecimalField(max_digits=40, decimal_places=10, default=0)
    largest_sell_net_loss = models.DecimalField(max_digits=40, decimal_places=10, default=0)

    @property
    def winning_net_profit(self):
        return self.buy_winning_net_profit + self.sell_winning_net_profit
    
    @property
    def losing_net_profit(self):
        return self.buy_losing_net_profit + self.sell_losing_net_profit
    
    @property
    def buy_winning_profit(self):
        return self.buy_winning_net_profit + abs(self.buy_winning_fees)

    @property
    def sell_winning_profit(self):
        return self.sell_winning_net_profit + abs(self.sell_winning_fees)

    @property
    def buy_losing_profit(self):
        return self.buy_losing_net_profit + abs(self.buy_losing_fees)

    @property
    def sell_losing_profit(self):
        return self.sell_losing_net_profit + abs(self.sell_losing_fees)
    
    @property
    def buy_profit(self):
        return self.buy_winning_profit + self.buy_losing_profit
    
    @property
    def sell_profit(self):
        return self.sell_winning_profit + self.sell_losing_profit
    
    @property
    def buy_fees(self):
        return abs(self.buy_winning_fees) + abs(self.buy_losing_fees)
    
    @property
    def sell_fees(self):
        return abs(self.sell_winning_fees) + abs(self.sell_losing_fees)
    
    @property
    def total_profit(self):
        return self.buy_profit + self.sell_profit
    
    @property
    def total_fees(self):
        return self.buy_fees + self.sell_fees
    
    @property
    def buy_net_profit(self):
        return self.buy_winning_net_profit + self.buy_losing_net_profit
    
    @property
    def sell_net_profit(self):
        return self.sell_winning_net_profit + self.sell_losing_net_profit
    
    @property
    def net_profit(self):
        return self.buy_net_profit + self.sell_net_profit
    
    @property
    def buy_profit_factor(self):
        return (self.buy_winning_net_profit / abs(self.buy_losing_net_profit)) if self.buy_losing_net_profit != 0 else Decimal("0")

    @property
    def sell_profit_factor(self):
        return (self.sell_winning_net_profit / abs(self.sell_losing_net_profit)) if self.sell_losing_net_profit != 0 else Decimal("0")
    
    @property
    def profit_factor(self):
        return (self.winning_net_profit / abs(self.losing_net_profit)) if self.losing_net_profit != 0 else Decimal("0")

    @property
    def largest_net_profit(self):
        return max(self.largest_buy_net_profit, self.largest_sell_net_profit)
    
    @property
    def largest_net_loss(self):
        return min(self.largest_buy_net_loss, self.largest_sell_net_loss)

    @classmethod
    def with_totals_pnl(cls):
        return cls.objects.annotate(
            buy_profit=F("buy_winning_net_profit") - F("buy_winning_fees") + F("buy_losing_net_profit") - F("buy_losing_fees"),
            sell_profit=F("sell_winning_net_profit") - F("sell_winning_fees") + F("sell_losing_net_profit") - F("sell_losing_fees"),
            total_profit=(F("buy_winning_net_profit") - F("buy_winning_fees") + F("buy_losing_net_profit") - F("buy_losing_fees")) +
                         (F("sell_winning_net_profit") - F("sell_winning_fees") + F("sell_losing_net_profit") - F("sell_losing_fees")),
            buy_fees=F("buy_winning_fees") + F("buy_losing_fees"),
            sell_fees=F("sell_winning_fees") + F("sell_losing_fees"),
            total_fees=F("buy_winning_fees") + F("buy_losing_fees") + F("sell_winning_fees") + F("sell_losing_fees"),
            net_buy_profit=(F("buy_winning_net_profit") + F("buy_losing_net_profit")) - (F("buy_winning_fees") + F("buy_losing_fees")),
            net_sell_profit=(F("sell_winning_net_profit") + F("sell_losing_net_profit")) - (F("sell_winning_fees") + F("sell_losing_fees")),
            net_profit=((F("buy_winning_net_profit") + F("buy_losing_net_profit")) - (F("buy_winning_fees") + F("buy_losing_fees"))) +
                        ((F("sell_winning_net_profit") + F("sell_losing_net_profit")) - (F("sell_winning_fees") + F("sell_losing_fees"))),  
        )

    @classmethod
    def apply_trade_and_profit_stats(cls, perf_id, *, trade):
        """
        Atomic update of profit and fees.
        """
    
        net_profit = trade.net_profit
        profit = trade.profit
        fees = trade.fees
        side = trade.side

        is_a_win = net_profit > 0
        is_a_loss = net_profit < 0

        update_kwargs = {}

        # BUY side
        if side == "B":
            if is_a_win:
                update_kwargs["largest_buy_net_profit"] = Greatest(
                    F("largest_buy_net_profit"),
                    Value(Decimal(net_profit))
                )
            elif is_a_loss:
                update_kwargs["largest_buy_net_loss"] = Least(
                    F("largest_buy_net_loss"),
                    Value(Decimal(net_profit))
                )

        # SELL side
        elif side == "S":
            if is_a_win:
                update_kwargs["largest_sell_net_profit"] = Greatest(
                    F("largest_sell_net_profit"),
                    Value(Decimal(net_profit))
                )
            elif is_a_loss:
                update_kwargs["largest_sell_net_loss"] = Least(
                    F("largest_sell_net_loss"),
                    Value(Decimal(net_profit))
                )

        return cls.objects.filter(id=perf_id).update(
            buy_total_trades=F("buy_total_trades") + (1 if side == "B" else 0),
            buy_winning_trades=F("buy_winning_trades") + (1 if side == "B" and is_a_win else 0),
            buy_losing_trades=F("buy_losing_trades") + (1 if side == "B" and is_a_loss else 0),

            sell_total_trades=F("sell_total_trades") + (1 if side == "S" else 0),
            sell_winning_trades=F("sell_winning_trades") + (1 if side == "S" and is_a_win else 0),
            sell_losing_trades=F("sell_losing_trades") + (1 if side == "S" and is_a_loss else 0),

            buy_winning_net_profit=F("buy_winning_net_profit") + (Decimal(str(net_profit)) if side == "B" and is_a_win else 0),
            sell_winning_net_profit=F("sell_winning_net_profit") + (Decimal(str(net_profit)) if side == "S" and is_a_win else 0),
            buy_losing_net_profit=F("buy_losing_net_profit") + (Decimal(str(net_profit)) if side == "B" and is_a_loss else 0),
            sell_losing_net_profit=F("sell_losing_net_profit") + (Decimal(str(net_profit)) if side == "S" and is_a_loss else 0),

            buy_winning_fees=F("buy_winning_fees") + (Decimal(str(fees)) if side == "B" and is_a_win else 0),
            sell_winning_fees=F("sell_winning_fees") + (Decimal(str(fees)) if side == "S" and is_a_win else 0),
            buy_losing_fees=F("buy_losing_fees") + (Decimal(str(fees)) if side == "B" and is_a_loss else 0),
            sell_losing_fees=F("sell_losing_fees") + (Decimal(str(fees)) if side == "S" and is_a_loss else 0),

            **update_kwargs
        )
    class Meta:
        abstract = True


class AssetCurrencyPerformance(CurrencyBasePerformance):
    asset_performance = models.ForeignKey(
        AssetPerformance,
        on_delete=models.CASCADE,
        related_name="currencies"
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset_performance", "currency"],
                name="unique_asset_currency"
            )
        ]

    def __str__(self):
        return f"{self.currency} ({self.asset_performance_id})"


class StrategyCurrencyPerformance(CurrencyBasePerformance):
    strategy_performance = models.ForeignKey(
        StrategyPerformance,
        on_delete=models.CASCADE,
        related_name="currencies"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["strategy_performance", "currency"],
                name="unique_strategy_currency"
            )
        ]

    def __str__(self):
        return f"{self.currency} ({self.strategy_performance_id})"


class DayCurrencyPerformance(CurrencyBasePerformance):
    day_performance = models.ForeignKey(
        DayPerformance,
        on_delete=models.CASCADE,
        related_name="currencies"
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["day_performance", "currency"],
                name="unique_day_currency"
            )
        ]

    def __str__(self):
        return f"{self.currency} ({self.day_performance_id})"
    
class AccountCurrencyPerformance(CurrencyBasePerformance):
    account_performance = models.ForeignKey(
        AccountPerformance,
        on_delete=models.CASCADE,
        related_name="currencies"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account_performance", "currency"],
                name="unique_account_currency"
            )
        ]

    def __str__(self):
        return f"{self.currency} ({self.account_performance_id})"
    