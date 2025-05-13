from django.contrib import admin
from .models import *

from unfold.admin import ModelAdmin
# Register your models here.

@admin.register(CryptoBrokerAccount)
class CryptoBrokerAccountAdmin(ModelAdmin):
    list_display = ('name', 'custom_id', 'broker_type', 'created_at') 
    search_fields = ['name', 'custom_id'] 

@admin.register(ForexBrokerAccount)
class ForexBrokerAccountAdmin(ModelAdmin):
    list_display = ('name', 'custom_id', 'broker_type', 'created_at') 
    search_fields = ['name', 'custom_id', 'username'] 


@admin.register(LogMessage)
class LogMessageAdmin(ModelAdmin):
    pass


@admin.register(TradeDetails)
class TradeDetailsAdmin(ModelAdmin):
    pass

