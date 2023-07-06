from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home, name="home"),
    path('membership/', membership, name="membership"),
    path('membership/create', create_subscription_stripeform, name="membership-create"),
    path('profile/', get_profile, name='profile'),
    path('profile/update/tradingview_username', edit_tradingview_username, name='update-tradingview-username'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    # path('forget-password/', forget_password, name='forget-password'),
    path('reset-password', auth_views.PasswordResetView.as_view(template_name="profile_user/auth/reset_password.html"), name='reset_password'),
    path('reset-password-sent', auth_views.PasswordResetDoneView.as_view(template_name="profile_user/auth/reset_password_sent.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name="profile_user/auth/reset_password_confirm.html"), name='password_reset_confirm'),
    path('reset-password-done', auth_views.PasswordResetCompleteView.as_view(template_name="profile_user/auth/reset_password_done.html"), name='password_reset_complete'),
]