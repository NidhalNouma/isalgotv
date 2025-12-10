from django.shortcuts import render, redirect
from automate.functions.brokers.ctrader import CLIENT_ID as CTRADER_CLIENT_ID
from automate.functions.brokers.deriv import APP_ID as DERIV_APP_ID

# Create your views here.

def index(request):
    return render(request, "docs/index.html")

def instalation(request):
    return render(request, "docs/instalation.html")

def setup(request):
    return render(request, "docs/setup.html")

def share(request):
    return render(request, "docs/share.html")

def alerts(request):
    return render(request, "docs/alerts.html")

def alerts_placeholders(request):
    return render(request, "docs/alerts_placeholders.html")

def alerts_create(request):
    return render(request, "docs/alerts_create.html")

def automate(request):
    return render(request, "docs/automate.html")

def automate_playground(request):
    return render(request, "docs/automate_playground.html")

def automate_notes(request):
    return render(request, "docs/automate_notes.html")

def automate_binance(request):
    return render(request, "docs/automate_binance.html")

def automate_binanceus(request):
    return render(request, "docs/automate_binanceus.html")

def automate_bitget(request):
    return render(request, "docs/automate_bitget.html")

def automate_bybit(request):
    return render(request, "docs/automate_bybit.html")

def automate_crypto(request):
    return render(request, "docs/automate_crypto.html")

def automate_mexc(request):
    return render(request, "docs/automate_mexc.html")

def automate_bingx(request):
    return render(request, "docs/automate_bingx.html")

def automate_bitmart(request):
    return render(request, "docs/automate_bitmart.html")

def automate_kucoin(request):
    return render(request, "docs/automate_kucoin.html")

def automate_okx(request):
    return render(request, "docs/automate_okx.html")

def automate_kraken(request):
    return render(request, "docs/automate_kraken.html")

def automate_apex(request):
    return render(request, "docs/automate_apex.html")

def automate_hyperliquid(request):
    return render(request, "docs/automate_hyperliquid.html")

def automate_coinbase(request):
    return render(request, "docs/automate_coinbase.html")

def automate_tradelocker(request):
    return render(request, "docs/automate_tradelocker.html")

def automate_ctrader(request):
    context = {
        "ctrader_client_id": CTRADER_CLIENT_ID,
    }
    return render(request, "docs/automate_ctrader.html", context=context)

def automate_deriv(request):
    context = {
        "deriv_app_id": DERIV_APP_ID,
    }
    return render(request, "docs/automate_deriv.html", context=context)

def automate_hankotrade(request):
    return render(request, "docs/automate_hankotrade.html")

def automate_alpaca(request):
    return render(request, "docs/automate_alpaca.html")

def automate_metatrader4(request):
    return render(request, "docs/automate_metatrader4.html")

def automate_metatrader5(request):
    return render(request, "docs/automate_metatrader5.html")

def question(request):
    return render(request, "docs/question.html")

def contactus(request):
    return render(request, "docs/contactus.html")

def disclaimer(request):
    return render(request, "docs/disclaimer.html")

def terms_of_use(request):
    return render(request, "docs/terms_of_use.html")

def privacy_policy(request):
    return render(request, "docs/privacy_policy.html")