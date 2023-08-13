from django.contrib import admin
from .models import Strategy, StrategyImages, StrategyComments, StrategyResults, Replies

# Register your models here.

admin.site.register(StrategyImages)
admin.site.register(Replies)
admin.site.register(StrategyResults)
admin.site.register(StrategyComments)
admin.site.register(Strategy)
