from django.shortcuts import render, redirect
from django.contrib import messages
   
from django.http import HttpResponse
import os

from django.contrib.auth import logout

from django.conf import settings

from allauth.socialaccount.views import SignupView


from profile_user.views import random_strategies_results_context

class CustomSocialSignupView(SignupView):
    def get_success_url(self):
        print('Signup successful with Google ...')
        # Redirect to home after successful signup
        return redirect('home')

def index(request):
    import random
    if request.user.is_authenticated:
        return redirect('home')
    
    context = {'prices': settings.PRICES, **random_strategies_results_context() }
    
    template = random.choice(["main_app/index.html", "profile_user/home.html"])
    return render(request, template, context)


def redirect_to_home(request):
    return redirect('home')

def redirect_social(request):
    # messages.error(request, "Email already exists")
    return redirect('login')

def redirect_admin_login(request):
    return redirect('login')

def redirect_admin_logout(request):
    logout(request)
    return redirect('login')
