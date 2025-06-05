from django.shortcuts import render, redirect

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

def automate_coinbase(request):
    return render(request, "docs/automate_coinbase.html")

def automate_tradelocker(request):
    return render(request, "docs/automate_tradelocker.html")

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