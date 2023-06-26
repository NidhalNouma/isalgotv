from django.urls import path
from .views import *

urlpatterns = [
    path('membership/', membership, name="membership"),
    path('profile/', get_profile, name='profile'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('forget-password/', forget_password, name='forget-password'),
]