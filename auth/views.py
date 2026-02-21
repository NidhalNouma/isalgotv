from urllib.parse import urlparse

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.decorators.http import require_http_methods

from profile_user.models import User_Profile
from auth.forms import UserCreationEmailForm


def _is_safe_redirect(url):
    """Allow relative paths and full URLs on trusted subdomains."""
    if url and url.startswith('/'):
        return True
    try:
        parsed = urlparse(url)
        parent = getattr(settings, 'PARENT_HOST', '')
        if parent and parsed.hostname and parsed.hostname.endswith('.' + parent):
            return True
    except Exception:
        pass
    return False


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationEmailForm(request.POST) 
        try:
            if form.is_valid():
                user = form.save(commit=False)
                user.email = user.username
                user.save()
                User_Profile.objects.create(user = user)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                next_url = request.POST.get('next', '')
                if next_url and _is_safe_redirect(next_url):
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, "An error occurred while registering")

        except Exception as e:
            print("An error occurred while registering", e)
            messages.error(request, "An error occurred while registering")

    return render(request,'auth/register.html', {'form': form})

def logout_user(request):
    logout(request)

    # Clear any stored messages
    storage = messages.get_messages(request)
    for _ in storage:
        pass 

    referer_url = request.META.get('HTTP_REFERER')
    return redirect(referer_url if referer_url else 'index')

def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username = email)
        except Exception as e:
            messages.error(request, "User does not exist!")
            return render(request, 'auth/login.html')

        user = authenticate(request, username = email, password = password)
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            next_url = request.POST.get('next', '')
            if next_url and _is_safe_redirect(next_url):
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, "Email or Password incorrect!")

    return render(request, 'auth/login.html')

@require_http_methods([ "POST"])
def update_user_password(request):
    if request.user.is_authenticated:
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return render(request, 'include/settings/password.html', {'msg': 'Password updated succesfully!'})

        return render(request, 'include/settings/password.html', {'form': form})
