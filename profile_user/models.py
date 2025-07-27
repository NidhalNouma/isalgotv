from django.db import models
from django.contrib.auth.models import User

from django.db.models import Max
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from django.db import transaction
from django.utils.timezone import now

import json

from .utils.stripe import get_profile_data, delete_customer

from django.conf import settings
PRICE_LIST = settings.PRICE_LIST

# Create your models here.
class PrettyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, indent, sort_keys, **kwargs):
        super().__init__(*args, indent=4, sort_keys=True, **kwargs)

class User_Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True)
    bio = models.TextField(max_length=1000, blank=True)
    tradingview_username = models.CharField(max_length=100, blank=True)
    discord_username = models.CharField(max_length=100, blank=True)
    strategies = models.ManyToManyField(to='strategies.Strategy', blank=True)

    customer_id = models.CharField(max_length=100, blank=True)
    subscription_id = models.CharField(max_length=100, blank=True)
    has_subscription = models.BooleanField(default=False)
    
    stripe_obj = models.JSONField(blank=True, null=True, encoder=PrettyJSONEncoder)
    stripe_last_checked = models.DateTimeField(blank=True, null=True)


    is_lifetime = models.BooleanField(default=False)
    lifetime_num = models.IntegerField(default=0)
    lifetime_intent = models.CharField(default="", max_length=100, blank=True)
    
    ai_tokens_available = models.IntegerField(default=0, blank=True)  
    ai_free_daily_tokens_available = models.IntegerField(default=0, blank=True)  
    last_token_reset = models.DateField(default=now, blank=True) 

    def save(self, *args, **kwargs):
        # Check if is_lifetime changed from False to True
        if self.lifetime_num == 0 and self.is_lifetime:

            highest_lifetime_num = User_Profile.objects.aggregate(Max('lifetime_num'))['lifetime_num__max']
            lifetime_num = 1
            if highest_lifetime_num:
                lifetime_num = highest_lifetime_num + 1
            self.lifetime_num += lifetime_num
        super().save(*args, **kwargs)

    def reset_token_usage_if_needed(self):
        """Reset the token usage if the date has changed."""
        if self.last_token_reset != now().date():
            if self.has_subscription or self.is_lifetime:
                # Reset daily tokens only if the user has a subscription or is lifetime
                self.ai_free_daily_tokens_available = 500000
            else:
                # Reset to 0 if the user does not have a subscription or is not lifetime
                self.ai_free_daily_tokens_available = 50000
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

    def get_with_update_stripe_data(self, force = False):
        """
        Fetches Stripe customer, subscription, payment methods, and latest payment intent,
        then caches them in stripe_obj with a timestamp.
        """
        try:

            if not force and self.stripe_obj:
                customer = self.stripe_obj.get("customer", None)
                subscription = self.stripe_obj.get("subscription", None)

                if (customer and customer.get("id", None) != self.customer_id) or (not customer and self.customer_id): 
                    force = True

                if not self.is_lifetime:
                    if (subscription and subscription.get("id", None) != self.subscription_id) or (not subscription and self.subscription_id):
                        force = True

            if not force and self.stripe_obj and self.stripe_last_checked:
                # Check if the cached data is still valid (e.g., within 1 hour)
                if (now() - self.stripe_last_checked).total_seconds() < (3600 * 24):
                    return self


            print("Fetching Stripe data for user:", self.user.email)

            data = get_profile_data(self, PRICE_LIST)
            has_subscription = data.get("has_subscription", False)

            # Cache the result and timestamp
            self.stripe_obj = data
            self.has_subscription = has_subscription
            self.stripe_last_checked = now()
            self.save(update_fields=["stripe_obj", "stripe_last_checked", "has_subscription"])
            return self
        except Exception as e:
            print('Error fetching Stripe data ', e)
    

@receiver(pre_delete, sender=User_Profile)
def cleanup_stripe_on_profile_delete(sender, instance, **kwargs):
    """
    Runs before a User_Profile is deleted (including via cascade).
    Cancels Stripe subscription and deletes Stripe customer.
    """
    # Delete Stripe customer if exists automatically cancel subscription
    delete_customer(instance)


class Notification(models.Model):
    user = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    message = models.TextField()
    url = models.TextField(blank=True, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)