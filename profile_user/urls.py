from django.urls import path
from profile_user.views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/', home, name="home"),
    path('membership/', membership, name="membership"),
    path('membership/payment_method/create/', create_payment_method, name="payment_method-create"),
    path('membership/payment_method/delete/', delete_payment_method, name="payment_method-delete"),
    path('membership/payment_method/set_default/', setdefault_payment_method, name="payment_method-set-default"),
    path('membership/create/', subscription_stripeform, name="membership-create"),
    path('membership/update/', subscription_stripeform, name="membership-update"),
    path('membership/cancel/', cancel_subscription, name="membership-cancel"),
    path('membership/coupon/', check_coupon, name="membership-coupon"),
    path('membership/payment-intent/', create_setup_intent, name="membership-payment-intent"),
    path('stripe/webhook/', stripe_webhook, name="stripe-webhook"),
    path('profile/', get_profile, name='profile'),
    path('profile/update/tradingview_username', edit_tradingview_username, name='update-tradingview-username'),
    path('profile/update/discord_username', edit_discord_username, name='update-discord-username'),
    path('notifications/', notifications_page, name='notifications'),
    path('settings/', settings_page, name='settings'),
    path('access/', access_page, name='access'),
    path('give_access/<int:strategy_id>/', get_access, name='give_access'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('change-password/', update_user_password, name='change-password'),
    path('reset-password', auth_views.PasswordResetView.as_view(template_name="profile_user/auth/reset_password.html"), name='reset_password'),
    path('reset-password-sent', auth_views.PasswordResetDoneView.as_view(template_name="profile_user/auth/reset_password_sent.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name="profile_user/auth/reset_password_confirm.html"), name='password_reset_confirm'),
    path('reset-password-done', auth_views.PasswordResetCompleteView.as_view(template_name="profile_user/auth/reset_password_done.html"), name='password_reset_complete'),

    # path('preview-email/', preview_email, name='preview_email'),
    path('send-email/', send_email, name='send_email'),
]