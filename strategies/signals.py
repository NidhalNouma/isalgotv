from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Strategy
from django.contrib.auth.models import User

from profile_user.utils.send_mails import *
from .tasks import send_strategy_email_to_all_users

@receiver(post_save, sender=Strategy)
def strategy_post_save(sender, instance, created, **kwargs):
    if created:
        # Send Emails to all users about the new added
        pass

@receiver(pre_save, sender=Strategy)
def capture_pre_save_state(sender, instance, **kwargs):
    # Store the old value if the instance already exists
    if instance.pk:
        instance._pre_save_instance = sender.objects.get(pk=instance.pk).is_live
    else:
        instance._pre_save_instance = None

@receiver(post_save, sender=Strategy)
def check_is_live_change(sender, instance, created, **kwargs):
    old_is_live = getattr(instance, '_pre_save_instance', None)
    new_is_live = instance.is_live
    
    # Check if 'is_live' was changed from False to True
    if old_is_live is False and new_is_live is True:
        send_strategy_email_to_all_users.delay(instance.name, 'https://www.isalgo.com/strategies/' + instance.slug, instance.tradingview_url, instance.image_url)
        # # Retrieve all users from the database
        # users = User.objects.all()
        # # Loop through each user and print their email
        # print('Sending email to all users for the new strategy ', instance.name)
        # for user in users:
        #     new_strategy_mail(user.email, instance.name, 'https://www.isalgo.com/strategies/' + instance.slug, instance.tradingview_url, instance.image_url)

