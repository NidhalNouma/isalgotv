from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include
from .views import *
from auth.urls import *
from django.contrib.auth import views as auth_views
from profile_user.views import create_setup_intent

from automate.views import (
    get_accounts_list_json,
)

urlpatterns = [
    path('accounts/', include('allauth.urls')),
]

urlpatterns += i18n_patterns(
    path('', index, name='tero_index'),
    path('', index, name='home'),
    path('chat/', index, name='tero_index_chat'),
    path('chat', index),
    path('c/<int:id>/', chat_index, name='tero_chat_id'),
    path('c/<int:id>', chat_index),
    path('trade/', index, name='tero_index_trade'),
    path('trade', index),

    path('my/membership/payment-intent/', create_setup_intent, name="membership-payment-intent"),

    path('chat/sessions/create/', create_chat, name='ai_chat_sessions_create'),
    path('chat/sessions/<int:session_id>/update/', update_chat, name='ai_chat_sessions_update'),
    path('chat/sessions/<int:session_id>/read/', chat_read, name='ai_chat_sessions_read'),
    path('chat/sessions/<int:session_id>/delete/', delete_chat, name='ai_chat_sessions_delete'),
    path('chat/sessions/<int:start>/', get_chat_sessions, name='ai_chat_sessions'),

    path('chat/messages/<int:session_id>/<int:start>/', get_chat_messages, name='ai_chat_messages'),
    path('chat/messages/<int:session_id>/send/', new_chat_message, name='ai_chat_send_message'),
    path('chat/messages/<int:message_id>/like/', like_message, name='ai_chat_like_message'),
    path('chat/messages/<int:message_id>/dislike/', dislike_message, name='ai_chat_dislike_message'),

    path('chat/messages/<int:message_id>/branch/', branch_message, name='ai_chat_branch_message'),
    path('chat/messages/<int:message_id>/switch/', switch_branch, name='ai_chat_switch_branch'),

    path('chat/response/', ai_chat_view, name='ai_chat'),
    path('chat/stream_response/', stream_ai_reply, name='ai_stream_chat'),
    path('buy-tokens/', buy_ai_tokens, name='buy_ai_tokens'),

    path('trade/accounts/list/', get_accounts_list_json, name='trade_accounts_list'),


    # # Auth
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('change-password/', update_user_password, name='change-password'),
    path('reset-password', auth_views.PasswordResetView.as_view(template_name="profile_user/auth/reset_password.html"), name='reset_password'),
    path('reset-password-sent', auth_views.PasswordResetDoneView.as_view(template_name="profile_user/auth/reset_password_sent.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name="profile_user/auth/reset_password_confirm.html"), name='password_reset_confirm'),
    path('reset-password-done', auth_views.PasswordResetCompleteView.as_view(template_name="profile_user/auth/reset_password_done.html"), name='password_reset_complete'),
    
    path('404/', tero_404_preview, name='tero_404'),

    path('i18n/', include('django.conf.urls.i18n')),
    prefix_default_language=False,
)

handler404 = tero_404