"""
URL configuration for etradingview project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from .views import *


urlpatterns = [
    path('accounts/profile/', redirect_to_home),
    # path('accounts/google/login/callback/', redirect_to_home),
    path('accounts/', include('allauth.urls')),
    # path('accounts/social/signup/', CustomSocialSignupView.as_view(), name="redirect_social"),
    path('admin/login/', redirect_admin_login, name="redirect_admin_login"),
    path('admin/logout/', redirect_admin_logout, name="redirect_admin_logout"),
    path('', index, name='index'),
    
    path('admin/', admin.site.urls),
    path('my/', include('profile_user.urls')),
    path('strategies/', include('strategies.urls')) ,
    path('automate/', include('automate.urls')) ,
    path('docs/', include('docs.urls')),

# For Apple Pay
    path('.well-known/apple-developer-merchantid-domain-association', serve_apple_pay_verification),
]
