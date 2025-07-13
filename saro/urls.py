
from django.contrib import admin
from django.urls import path, include, re_path

from .views import *


urlpatterns = [
    path('', index, name='saro_index'),
    path('chat/', index, name='saro_chat'),
    path('trade/', index, name='saro_trade'),

    path('chat/sessions/create/', create_chat, name='ai_chat_sessions_create'),
    path('chat/sessions/<int:session_id>/update/', update_chat, name='ai_chat_sessions_update'),
    path('chat/sessions/<int:session_id>/delete/', delete_chat, name='ai_chat_sessions_delete'),
    path('chat/sessions/<int:start>/', get_chat_sessions, name='ai_chat_sessions'),

    path('chat/messages/<int:session_id>/<int:start>/', get_chat_messages, name='ai_chat_messages'),
    path('chat/messages/<int:session_id>/send/', new_chat_message, name='ai_chat_send_message'),

    path('chat/response/', ai_chat_view, name='ai_chat'),
    path('buy-tokens/', buy_ai_tokens, name='buy_ai_tokens'),
    path('chat/system-content/', get_ai_system_content, name='ai_system_content'),

]