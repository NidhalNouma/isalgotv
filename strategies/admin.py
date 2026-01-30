from django.contrib import admin
from .models import Strategy, StrategyPrice, StrategyImages, StrategyComments, StrategyResults, Replies

from unfold.admin import ModelAdmin

# Register your models here.
@admin.register(StrategyImages)
class StrategyImagesAdmin(ModelAdmin):
    pass

@admin.register(Replies)
class RepliesAdmin(ModelAdmin):
    pass

@admin.register(StrategyResults)
class StrategyResultsAdmin(ModelAdmin):
    pass

@admin.register(StrategyComments)
class StrategyCommentsAdmin(ModelAdmin):
    pass

@admin.register(Strategy)
class StrategyAdmin(ModelAdmin):
    list_display = ('name', 'premium', 'created_by', 'created_at')
    search_fields = ['name', 'created_by__user__username']

@admin.register(StrategyPrice)
class StrategyPriceAdmin(ModelAdmin):
    list_display = ('strategy', 'amount', 'currency', 'interval', 'interval_count')
    search_fields = ['strategy__name', 'currency']