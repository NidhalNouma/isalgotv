from django.db.models.signals import post_save, post_init, pre_save
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from profile_user.models import User_Profile

from profile_user.tasks import send_welcome_email_task, send_amount_to_pay_email_task


@receiver(user_signed_up)
def send_welcome_email_allauth(request, user, **kwargs):
    print('new user sign up ... ', user.email)

@receiver(post_save, sender=User_Profile)
def user_profile_save(sender, instance, created, **kwargs):
    if created:
        # Send Emails to all users about the new added
        user_email = instance.user.email
        if user_email:
            # print('New user signal fired ...')
            send_welcome_email_task(user_email, user_email)
            # send_welcome_email_task.delay(user_email, user_email)

@receiver(post_init, sender=User_Profile)
def store_original_amount(sender, instance, **kwargs):
    instance._original_amount_to_pay = instance.amount_to_pay

@receiver(pre_save, sender=User_Profile)
def detect_amount_to_pay_change(sender, instance, **kwargs):
    if not hasattr(instance, '_original_amount_to_pay'):
        return

    if instance._original_amount_to_pay != instance.amount_to_pay:
        if instance.amount_to_pay > 0:
            print(f"amount_to_pay changed: {instance._original_amount_to_pay} → {instance.amount_to_pay}")
            send_amount_to_pay_email_task(instance.user.email, instance.amount_to_pay)