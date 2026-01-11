from django.contrib import admin
from performance.models import *

from unfold.admin import ModelAdmin


@admin.register(AccountPerformance)
class AccountPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Account"
    verbose_name_plural = "Performance - Accounts"

    list_display = ('id', 'get_account')
    search_fields = ['content_type__name', 'content_type__custom_id']
    
    def get_account(self, obj):
        return str(obj.content_type) if obj.content_type else '-'
    get_account.short_description = 'Account'

@admin.register(StrategyPerformance)
class StrategyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Strategy"
    verbose_name_plural = "Performance - Strategies"

    list_display = ('id', 'get_strategy_name', 'account_performance')
    search_fields = ['strategy__name', 'account_performance__content_type__name']
    
    def get_strategy_name(self, obj):
        return obj.strategy.name if obj.strategy else '-'
    get_strategy_name.short_description = 'Strategy Name'

@admin.register(AssetPerformance)
class AssetPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Asset"
    verbose_name_plural = "Performance - Assets"

    list_display = ('id', 'asset', 'account_performance')
    search_fields = ['asset', 'account_performance__content_type__name']

@admin.register(AccountCurrencyPerformance)
class AccountCurrencyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Account Currency"
    verbose_name_plural = "Performance - Account Currencies"

    list_display = ('id', 'currency', 'account_performance')
    search_fields = ['currency', 'account_performance__content_type__name']

@admin.register(DayPerformance)
class DayPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Day"
    verbose_name_plural = "Performance - Days"
    
    list_display = ('id', 'date', 'account_performance')
    search_fields = ['account_performance__content_type__model', 'account_performance__object_id']


# @admin.register(TradeAppliedPerformance)
# class TradeAppliedPerformanceAdmin(ModelAdmin):
#     verbose_name = "Trade Applied Performance"
#     verbose_name_plural = "Trade Applied Performances"
    
#     list_display = ('id', 'trade', 'performance_type', 'performance_id', 'applied_at')
#     search_fields = ['trade__symbol', 'performance_type']
#     list_filter = ['performance_type']


@admin.register(DayAssetPerformance)
class DayAssetPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Day Asset"
    verbose_name_plural = "Performance - Day Assets"
    
    list_display = ('id', 'asset_performance', 'day_performance', 'buy_total_trades', 'sell_total_trades')


@admin.register(DayStrategyPerformance)
class DayStrategyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Day Strategy"
    verbose_name_plural = "Performance - Day Strategies"
    
    list_display = ('id', 'strategy_performance', 'day_performance', 'buy_total_trades', 'sell_total_trades')


@admin.register(AssetStrategyPerformance)
class AssetStrategyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Asset Strategy"
    verbose_name_plural = "Performance - Asset Strategies"
    
    list_display = ('id', 'asset_performance', 'strategy_performance', 'buy_total_trades', 'sell_total_trades')


@admin.register(AssetCurrencyPerformance)
class AssetCurrencyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Asset Currency"
    verbose_name_plural = "Performance - Asset Currencies"
    
    list_display = ('id', 'currency', 'asset_performance', 'net_profit', 'profit_factor')
    search_fields = ['currency']
    list_filter = ['currency']


@admin.register(StrategyCurrencyPerformance)
class StrategyCurrencyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Strategy Currency"
    verbose_name_plural = "Performance - Strategy Currencies"
    
    list_display = ('id', 'currency', 'strategy_performance', 'net_profit', 'profit_factor')
    search_fields = ['currency']
    list_filter = ['currency']


@admin.register(DayCurrencyPerformance)
class DayCurrencyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Day Currency"
    verbose_name_plural = "Performance - Day Currencies"
    
    list_display = ('id', 'currency', 'day_performance', 'net_profit', 'profit_factor')
    search_fields = ['currency']
    list_filter = ['currency']


@admin.register(DayAssetCurrencyPerformance)
class DayAssetCurrencyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Day Asset Currency"
    verbose_name_plural = "Performance - Day Asset Currencies"
    
    list_display = ('id', 'currency', 'day_asset_performance', 'net_profit', 'profit_factor')
    search_fields = ['currency']
    list_filter = ['currency']


@admin.register(DayStrategyCurrencyPerformance)
class DayStrategyCurrencyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Day Strategy Currency"
    verbose_name_plural = "Performance - Day Strategy Currencies"
    
    list_display = ('id', 'currency', 'day_strategy_performance', 'net_profit', 'profit_factor')
    search_fields = ['currency']
    list_filter = ['currency']


@admin.register(AssetStrategyCurrencyPerformance)
class AssetStrategyCurrencyPerformanceAdmin(ModelAdmin):
    verbose_name = "Performance - Asset Strategy Currency"
    verbose_name_plural = "Performance - Asset Strategy Currencies"
    
    list_display = ('id', 'currency', 'asset_strategy_performance', 'net_profit', 'profit_factor')
    search_fields = ['currency']
    list_filter = ['currency']
    