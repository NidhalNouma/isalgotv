from django.contrib import admin
from .models import Strategy, StrategyImages, StrategyComments, StrategyResults, Replies

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
    pass