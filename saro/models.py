from django.db import models
from django.contrib.auth.models import User

class ChatSession(models.Model):
    """A single conversation between a user and the AI."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    # Optional summary for memory
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Session #{self.id} for {self.user.username}"

class ChatMessage(models.Model):
    """Individual messages in a conversation."""
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=50, choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')])
    content = models.TextField()
    
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')

    liked = models.BooleanField(null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional for vector search
    embedding = models.JSONField(blank=True, null=True)  # Or ArrayField if you're using pgvector


    def __str__(self):
        return f"{self.role.capitalize()} @ {self.created_at}"