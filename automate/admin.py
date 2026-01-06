from django.contrib import admin
from automate.models import *

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
    list_display = ('response_status',)
    search_fields = ['alert_message', 'response_message', 'response_status']


@admin.register(TradeDetails)
class TradeDetailsAdmin(ModelAdmin):
    list_display = ('symbol', 'side', 'volume', 'status')
    search_fields = ['symbol', 'side', 'status', 'order_id', 'custom_id']
