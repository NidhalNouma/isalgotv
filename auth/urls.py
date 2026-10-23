from django.urls import path
from django.contrib.auth import views as auth_views

from auth.views import register, login_user, logout_user, update_user_password, verify_email, resend_verification_email, verify_required

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('verify-email/<str:token>/', verify_email, name='verify_email'),
    path('verify-required/', verify_required, name='verify_required'),
    path('resend-verification/', resend_verification_email, name='resend_verification'),
    path('logout/', logout_user, name='logout'),
    path('change-password/', update_user_password, name='change-password'),
    path('reset-password', auth_views.PasswordResetView.as_view(template_name="auth/reset_password.html"), name='reset_password'),
    path('reset-password-sent', auth_views.PasswordResetDoneView.as_view(template_name="auth/reset_password_sent.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name="auth/reset_password_confirm.html"), name='password_reset_confirm'),
    path('reset-password-done', auth_views.PasswordResetCompleteView.as_view(template_name="auth/reset_password_done.html"), name='password_reset_complete'),
]
