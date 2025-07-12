from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='saro_index_landing'),
    path('chat/', index, name='saro_index_chat'),
    path('trade/', index, name='saro_index_trade'),
]