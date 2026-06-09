from django.contrib import admin

from .models import *

from unfold.admin import ModelAdmin
# Register your models here.

@admin.register(ChatSession)
class ChatSessionAdmin(ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'last_updated') 
    search_fields = ['title', 'user__username'] 

@admin.register(ChatMessage)
class ChatMessageAdmin(ModelAdmin):
    list_display = ('session', 'role', 'created_at', 'liked') 
    search_fields = ['session__title', 'content'] 
    list_filter = ('role', 'liked') 
    raw_id_fields = ('session',)