from django.db import models
from django.contrib.auth.models import User

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from django.db import transaction
from django.utils.timezone import now

import datetime
import time
import json

import environ
env = environ.Env()

from django.conf import settings
PRICE_LIST = settings.PRICE_LIST

import stripe
stripe.api_key = env('STRIPE_API_KEY')


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

    def get_with_update_stripe_data(self, force = False):
        """
        Fetches Stripe customer, subscription, payment methods, and latest payment intent,
        then caches them in stripe_obj with a timestamp.
        """

        if not force and self.stripe_obj:
            customer = self.stripe_obj.get("customer", None)
            subscription = self.stripe_obj.get("subscription", None)

            if (customer and customer.get("id", None) != self.customer_id) or (not customer and self): 
                force = True

            if (subscription and subscription.get("id", None) != self.subscription_id) or (not subscription and self.subscription_id):
                force = True


        if not force and self.stripe_obj and self.stripe_last_checked:
            # Check if the cached data is still valid (e.g., within 1 hour)
            if (now() - self.stripe_last_checked).total_seconds() < (3600 * 24):
                return self


        print("Fetching Stripe data for user:", self.user.email)


        data = {
            "customer": None,
            "subscription": None,
            "payment_methods": None,
            "payment_intent": None,
            "subscription_canceled": False,
            "subscription_next_payment_amount": None,
            "subscription_period_end": None,
            "subscription_active": False,
            "subscription_status": None,
            "subscription_price_id": None,
            "subscription_product_id": None,
            "subscription_interval": None,
            "subscription_interval_count": None,
            "subscription_plan": None,
        }
    
        try:
            if self.customer_id:
                try:
                    stripe_customer = stripe.Customer.retrieve(self.customer_id)
                    # print("stripe customer, " , stripe_customer)
                except Exception as e:
                    print("Error with getting stripe customer...", e)

            if not self.customer_id or not stripe_customer or "deleted" in stripe_customer:
                customer = stripe.Customer.create(
                        email=self.user.email,
                        name=self.user.username,
                    )
                if customer.id:
                    stripe_customer = customer
                    # user_profile = User_Profile.objects.get(user=current_user)
                    self.customer_id = customer.id
                    self.save(update_fields=["customer_id"])

            data["customer"] = stripe_customer

            if self.is_lifetime:
                self.has_subscription = True

            # Retrieve subscription if exists
            if self.subscription_id:
                subscription = stripe.Subscription.retrieve(self.subscription_id)
                data["subscription"] = subscription


                end_timestamp = subscription.current_period_end * 1000
                end_time = datetime.datetime.fromtimestamp(end_timestamp / 1e3)


                subscription_status = subscription.status

                subscription_interval = subscription.plan.interval
                subscription_interval_count = subscription.plan.interval_count


                data["subscription_period_end"] = end_time.isoformat()
                data["subscription_active"] = subscription.plan.active
                data["subscription_status"] = subscription.status
                data["subscription_price_id"] = subscription.plan.id
                data["subscription_product_id"] = subscription.plan.product
                data["subscription_interval"] = subscription.plan.interval
                data["subscription_interval_count"] = subscription.plan.interval_count


                if subscription_interval == "year":
                    subscription_plan = list(PRICE_LIST.keys())[2]

                elif subscription_interval == "month":
                    if subscription_interval_count == 1:
                        subscription_plan = list(PRICE_LIST.keys())[0]
                    elif subscription_interval_count == 3:
                        subscription_plan = list(PRICE_LIST.keys())[1]
                    elif subscription_interval_count == 12:
                        subscription_plan = list(PRICE_LIST.keys())[2]
                
                data["subscription_plan"] = subscription_plan
                


                if subscription_status == 'active' and subscription.current_period_end > time.time():
                    self.has_subscription = True
                elif subscription_status == 'trialing' and subscription.current_period_end > time.time():
                    self.has_subscription = True
                elif subscription_status == 'past_due' and subscription.current_period_end > time.time():
                    self.has_subscription = True
                # elif subscription.status == "canceled" and subscription.current_period_end > time.time():
                #     has_subscription = True
                elif subscription_status == "incomplete":
                    self.has_subscription = False

                
                if subscription.cancel_at_period_end or subscription.status == "canceled" or subscription.status == "incomplete":
                    data["subscription_canceled"] = True

                
                if not data["subscription_canceled"] and self.has_subscription:
                    # Get the upcoming invoice for the subscription
                    upcoming_invoice = stripe.Invoice.upcoming(subscription=subscription)
                    data["payment_intent"] = upcoming_invoice

                    if upcoming_invoice:
                        total_amount_due = upcoming_invoice["amount_due"]/100
                        data["subscription_next_payment_amount"] = total_amount_due


            if self.customer_id:
                try:
                    payment_methods = stripe.Customer.list_payment_methods(self.customer_id, limit=100)
                    payment_methods = payment_methods.data
                    data["payment_methods"] = payment_methods
                except Exception as e:
                    print("Error with getting payment methods ...", e)

        except Exception as e:
            print("Error with getting stripe data ...", e)

        # Cache the result and timestamp
        self.stripe_obj = data
        self.stripe_last_checked = now()
        self.save(update_fields=["stripe_obj", "stripe_last_checked", "has_subscription"])
        return self
    

@receiver(pre_delete, sender=User_Profile)
def cleanup_stripe_on_profile_delete(sender, instance, **kwargs):
    """
    Runs before a User_Profile is deleted (including via cascade).
    Cancels Stripe subscription and deletes Stripe customer.
    """
    # Delete Stripe customer if exists automatically cancel subscription
    if instance.customer_id:
        print(f"Deleting Stripe customer {instance.customer_id} for user {instance.user.email}")
        try:
            stripe.Customer.delete(instance.customer_id)
        except stripe.error.StripeError as e:
            # log or ignore Stripe deletion errors
            print(f"Error deleting Stripe customer {instance.customer_id}: {e}")


class Notification(models.Model):
    user = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    message = models.TextField()
    url = models.TextField(blank=True, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)