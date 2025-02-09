from django.urls import path
from .views import *

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

    path('get-sub-data/<str:broker_type>/<int:pk>/<str:account_subscription_id>/', account_subscription_data, name='get_account_subscription_data'),
    path('change-sub-payment/<str:broker_type>/<int:pk>/<str:account_subscription_id>/', change_account_subscription_payment, name='change_account_subscription_payment'),


    path('c/<str:custom_id>', handle_webhook_crypto, name='webhook_crypto_request'),
    path('f/<str:custom_id>', handle_webhook_forex, name='webhook_forex_request'),
]