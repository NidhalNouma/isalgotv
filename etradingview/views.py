from django.shortcuts import render, redirect
from django.contrib import messages

from django.contrib.auth import logout

from django.conf import settings

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    return render(request, "etradingview/index.html", context={'prices': settings.PRICES})


def redirect_social(request):
    messages.error(request, "Email already exists")
    return redirect('login')

def redirect_admin_login(request):
    return redirect('login')

def redirect_admin_logout(request):
    logout(request)
    return redirect('login')