from django.contrib import admin

from .models import *

# Register your models here.

class CryptoBrokerAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'custom_id', 'created_at') 
    search_fields = ['name', 'custom_id'] 

class ForexBrokerAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'custom_id', 'created_at') 
    search_fields = ['name', 'custom_id', 'username'] 

admin.site.register(CryptoBrokerAccount, CryptoBrokerAccountAdmin)
admin.site.register(ForexBrokerAccount, ForexBrokerAccountAdmin)

admin.site.register(LogMessage)
admin.site.register(TradeDetails)
# admin.site.register(CryptoLogMessage)
