from django.urls import path
from django.contrib.auth import views as auth_views

from auth.views import register, login_user, logout_user, update_user_password

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('change-password/', update_user_password, name='change-password'),
    path('reset-password', auth_views.PasswordResetView.as_view(template_name="auth/reset_password.html"), name='reset_password'),
    path('reset-password-sent', auth_views.PasswordResetDoneView.as_view(template_name="auth/reset_password_sent.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name="auth/reset_password_confirm.html"), name='password_reset_confirm'),
    path('reset-password-done', auth_views.PasswordResetCompleteView.as_view(template_name="auth/reset_password_done.html"), name='password_reset_complete'),
]
