from django.urls import path, include
from .views import *

from django.contrib.auth import views as auth_views
from profile_user.views import (
    create_setup_intent,
)

from automate.views import (
    get_accounts_list_json,
)

urlpatterns = [
    path('', index, name='home'),
    path('chat/', index, name='saro_index_chat'),
    path('chat', index),
    path('trade/', index, name='saro_index_trade'),
    path('trade', index),

    path('my/membership/payment-intent/', create_setup_intent, name="membership-payment-intent"),

    path('chat/sessions/create/', create_chat, name='ai_chat_sessions_create'),
    path('chat/sessions/<int:session_id>/update/', update_chat, name='ai_chat_sessions_update'),
    path('chat/sessions/<int:session_id>/read/', chat_read, name='ai_chat_sessions_read'),
    path('chat/sessions/<int:session_id>/delete/', delete_chat, name='ai_chat_sessions_delete'),
    path('chat/sessions/<int:start>/', get_chat_sessions, name='ai_chat_sessions'),

    path('chat/messages/<int:session_id>/<int:start>/', get_chat_messages, name='ai_chat_messages'),
    path('chat/messages/<int:session_id>/send/', new_chat_message, name='ai_chat_send_message'),

    path('chat/response/', ai_chat_view, name='ai_chat'),
    path('buy-tokens/', buy_ai_tokens, name='buy_ai_tokens'),

    path('trade/accounts/list/', get_accounts_list_json, name='trade_accounts_list'),

    # path('my/register/', register, name='register'),
    # path('my/login/', login_user, name='login'),
    # path('my/logout/', logout_user, name='logout'),
    # path('my/change-password/', update_user_password, name='change-password'),
    # # path('forget-password/', forget_password, name='forget-password'),
    # path('my/reset-password', auth_views.PasswordResetView.as_view(template_name="profile_user/auth/reset_password.html"), name='reset_password'),
    # path('my/reset-password-sent', auth_views.PasswordResetDoneView.as_view(template_name="profile_user/auth/reset_password_sent.html"), name='password_reset_done'),
    # path('my/reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name="profile_user/auth/reset_password_confirm.html"), name='password_reset_confirm'),
    # path('my/reset-password-done', auth_views.PasswordResetCompleteView.as_view(template_name="profile_user/auth/reset_password_done.html"), name='password_reset_complete'),
    # path('accounts/', include('allauth.urls')),
]