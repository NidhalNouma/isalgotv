from django.contrib import admin

from .models import CryptoBrokerAccount, CryptoLogMessage

# Register your models here.

class CryptoBrokerAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'custom_id', 'created_at') 
    search_fields = ['name', 'custom_id'] 

admin.site.register(CryptoBrokerAccount, CryptoBrokerAccountAdmin)
# admin.site.register(CryptoLogMessage)
