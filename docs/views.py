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

def automate(request):
    return render(request, "docs/automate.html")

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