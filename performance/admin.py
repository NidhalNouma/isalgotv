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
    