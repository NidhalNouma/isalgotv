from django.urls import path
from automate.views import *

urlpatterns = [
    # path('home/', home, name='home'),
    path('', index, name='automate'),
    path('add-crypto-broker/<str:broker_type>/', add_broker, name='add_crypto_broker_account'),
    path('edit-crypto-broker/<str:broker_type>/<int:pk>/', edit_broker, name='edit_crypto_broker_account'),

    path('add-forex-broker/<str:broker_type>/', add_broker, name='add_forex_broker_account'),
    path('edit-forex-broker/<str:broker_type>/<int:pk>/', edit_broker, name='edit_forex_broker_account'),

    path('toggle-broker/<str:broker_type>/<int:pk>/', toggle_broker, name='toggle_broker'),
    path('delete--broker/<str:broker_type>/<int:pk>/', delete_broker, name='delete_broker'),
    path('get-broker-logs/<str:broker_type>/<int:pk>/', get_broker_logs, name='get_logs'),
    path('get-broker-logs/<str:broker_type>/<int:pk>/export/', export_broker_logs, name='export_logs'),
    path('get-broker-trades/<str:broker_type>/<int:pk>/', get_broker_trades, name='get_trades'),
    path('broker/<str:broker_type>/<int:pk>/close-trade/<int:trade_id>/', close_trade, name='close_trade'),

    path('get-sub-data/<str:broker_type>/<int:pk>/<str:account_subscription_id>/', account_subscription_data, name='get_account_subscription_data'),
    path('change-sub-payment/<str:broker_type>/<int:pk>/<str:account_subscription_id>/', change_account_subscription_payment, name='change_account_subscription_payment'),

    path('accounts/list/', get_accounts_list_json, name='get_account_list_json'),

    path('ctrader/auth/', ctrader_auth_code, name='ctrader_auth_code'),


    path('c/<str:custom_id>', handle_webhook_crypto, name='webhook_crypto_request'),
    path('f/<str:custom_id>', handle_webhook_forex, name='webhook_forex_request'),
]