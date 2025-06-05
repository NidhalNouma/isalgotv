
from django.contrib import admin
from django.urls import path, include

from .views import *


urlpatterns = [
    path('Introduction/', index, name='docs_index'),
    path('instalation/', instalation, name='docs_instalation'),
    path('setup/', setup, name='docs_setup'),
    path('share/', share, name='docs_share'),

    path('alerts/', alerts, name='docs_alerts'),
    path('alerts/placeholders', alerts_placeholders, name='docs_alerts_placeholders'),
    path('alerts/create', alerts_create, name='docs_alerts_create'),

    path('automate/', automate, name='docs_automate'),
    path('automate/playground', automate_playground, name='docs_automate_playground'),
    path('automate/notes', automate_notes, name='docs_automate_notes'),
    path('automate/binance', automate_binance, name='docs_automate_broker_binance'),
    path('automate/binanceus', automate_binanceus, name='docs_automate_broker_binanceus'),
    path('automate/bitget', automate_bitget, name='docs_automate_broker_bitget'),
    path('automate/bybit', automate_bybit, name='docs_automate_broker_bybit'),
    path('automate/crypto', automate_crypto, name='docs_automate_broker_crypto'),
    path('automate/mexc', automate_mexc, name='docs_automate_broker_mexc'),
    path('automate/bingx', automate_bingx, name='docs_automate_broker_bingx'),
    path('automate/bitmart', automate_bitmart, name='docs_automate_broker_bitmart'),
    path('automate/kucoin', automate_kucoin, name='docs_automate_broker_kucoin'),
    path('automate/coinbase', automate_coinbase, name='docs_automate_broker_coinbase'),
    path('automate/tradelocker', automate_tradelocker, name='docs_automate_broker_tradelocker'),

    path('q&a/', question, name='docs_questions'),
    path('contact_us/', contactus, name='docs_contactus'),

    path('disclaimer/', disclaimer, name='docs_disclaimer'),
    path('terms-of-use/', terms_of_use, name='docs_terms_of_use'),
    path('privacy-policy/', privacy_policy, name='docs_privacy_policy')
]