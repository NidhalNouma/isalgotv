
from django.contrib import admin
from django.urls import path, include

from .views import *


urlpatterns = [
    path('', index, name='saro_index'),
    path('chat/', ai_chat_view, name='ai_chat'),
    path('buy-tokens/', buy_ai_tokens, name='buy_ai_tokens'),
    path('chat/system-content/', get_ai_system_content, name='ai_system_content'),
]