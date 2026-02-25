from django.urls import path
from profile_user.views import *

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
    path('pay/remaining-amount-payment-intent/', pay_remaining_amount, name="pay_remaining_amount"),
    path('stripe/webhook/', stripe_webhook, name="stripe-webhook"),
    path('stripe/webhook/connect/', stripe_webhook_connect, name="stripe-webhook-connect"),
    path('profile/', get_profile, name='profile'),
    path('profile/update/tradingview_username', edit_tradingview_username, name='update-tradingview-username'),
    path('profile/update/discord_username', edit_discord_username, name='update-discord-username'),
    path('notifications/', notifications_page, name='notifications'),
    path('settings/', settings_page, name='settings'),
    path('access/', access_page, name='access'),
    path('give_access/<int:strategy_id>/', get_access, name='give_access'),

    path('complete-seller-account-onboarding/', complete_seller_account_onboarding, name='complete_seller_account_onboarding'),
    path('stripe-seller-dashboard/', stripe_seller_dashboard, name='stripe_seller_dashboard'),

    # path('preview-email/', preview_email, name='preview_email'),
    path('send-email/', send_email, name='send_email'),

    path('api/send-marketing-email/', api_send_marketing_email, name='api_send_marketing_email'),
]