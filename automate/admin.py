from django.contrib import admin

from .models import CryptoBrokerAccount, TradeDetails

# Register your models here.

admin.site.register(CryptoBrokerAccount)
admin.site.register(TradeDetails)
