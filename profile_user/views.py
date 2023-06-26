from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout

from .models import User_Profile
from .forms import User_ProfileForm

# Create your views here.

def membership(request):
    return render(request, 'membership.html')

def register(request):
    if request.method == 'POST':
        form = User_ProfileForm(request.POST) 
        if form.is_valid():
            form.save(commit=False)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            user = username
            login(request, user)
            return redirect('home')

    return render(request,'register.html', {'form': User_ProfileForm()})

def login_user(request):
    return render(request, 'login.html')

def forget_password(request):
    return render(request, 'forget_password.html')

def get_profile(request):
    if request.user.is_authenticated:
        profile = User_Profile.objects.get(user=request.user)
        return render(request, 'profile.html', {'profile': profile})
    else:
        return render(request, 'profile.html')
    

def edit_profile(request):
    if request.user.is_authenticated:
        profile = User_Profile.objects.get(user=request.user)

        if request.method == 'POST':
            form = User_ProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return redirect('profile')

        return render(request, 'edit_profile.html', {'profile': profile})
    else:
        return render(request, 'edit_profile.html')