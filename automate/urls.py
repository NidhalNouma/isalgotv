from django.urls import path
from .views import *

urlpatterns = [
    # path('home/', home, name='home'),
    path('', index, name='automate'),
    path('add-crypto-broker/<str:broker_type>/', add_crypto_broker, name='add_crypto_broker_account'),
    path('edit-crypto-broker/<int:pk>/', edit_crypto_broker, name='edit_crypto_broker_account'),
    path('toggle-crypto-broker/<int:pk>/', toggle_crypto_broker, name='toggle_crypto_broker'),
    path('delete-crypto-broker/<int:pk>/', delete_crypto_broker, name='delete_crypto_broker'),
]