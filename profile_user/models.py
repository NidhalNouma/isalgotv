from django.db import models
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.timezone import now


# Create your models here.

class User_Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True)
    bio = models.TextField(max_length=1000, blank=True)
    tradingview_username = models.CharField(max_length=100, blank=True)
    discord_username = models.CharField(max_length=100, blank=True)
    strategies = models.ManyToManyField(to='strategies.Strategy', blank=True)

    subscription_id = models.CharField(max_length=100, blank=True)
    customer_id = models.CharField(max_length=100, blank=True)

    is_lifetime = models.BooleanField(default=False)
    lifetime_num = models.IntegerField(default=0)
    lifetime_intent = models.CharField(default="", max_length=100, blank=True)
    
    ai_tokens_available = models.IntegerField(default=0, blank=True)  
    ai_tokens_used_today = models.IntegerField(default=0, blank=True)  
    last_token_reset = models.DateField(default=now, blank=True) 

    def reset_token_usage_if_needed(self):
        """Reset the token usage if the date has changed."""
        if self.last_token_reset != now().date():
            self.ai_tokens_used_today = 0
            self.last_token_reset = now().date()
            self.save()

    def __str__(self):
        return self.user.username

    def get_tradingview_username(self):
        if self.tradingview_username:
            return self.tradingview_username
        return self.user.username

    def deactivate_all_accounts(self):
        from automate.models import CryptoBrokerAccount, ForexBrokerAccount
        with transaction.atomic():
            CryptoBrokerAccount.objects.filter(created_by=self).update(active=False)
            ForexBrokerAccount.objects.filter(created_by=self).update(active=False)

class Notification(models.Model):
    user = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    message = models.TextField()
    url = models.TextField(blank=True, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)