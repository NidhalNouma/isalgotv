from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Strategy
from django.contrib.auth.models import User

from profile_user.utils.send_mails import *
from .tasks import send_strategy_email_to_all_users

# @receiver(pre_save, sender=Strategy)
# def capture_pre_save_state(sender, instance, **kwargs):
#     # Store the old value if the instance already exists
#     if instance.pk:
#         instance._pre_save_instance = sender.objects.get(pk=instance.pk).is_live
#     else:
#         instance._pre_save_instance = None


# @receiver(post_save, sender=Strategy)
# def check_is_live_change(sender, instance, created, **kwargs):
#     old_is_live = getattr(instance, '_pre_save_instance', None)
#     new_is_live = instance.is_live
    


