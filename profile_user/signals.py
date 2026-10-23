from django.db.models.signals import post_save, post_init, pre_save
from allauth.account.signals import user_signed_up, user_logged_in
from django.dispatch import receiver
from profile_user.models import User_Profile

from profile_user.tasks import send_welcome_email_task, send_amount_to_pay_email_task


@receiver(user_signed_up)
def send_welcome_email_allauth(request, user, **kwargs):
    print('new user sign up ... ', user.email)

@receiver(user_logged_in)
def verify_email_on_social_login(request, user, sociallogin=None, **kwargs):
    # The provider (e.g. Google) already verified the address
    if sociallogin is None:
        return
    profile, _created = User_Profile.objects.get_or_create(user=user)
    if not profile.email_verified:
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])

@receiver(post_save, sender=User_Profile)
def user_profile_save(sender, instance, created, **kwargs):
    if created:
        # Send Emails to all users about the new added
        user_email = instance.user.email
        # Email/password signups get the welcome email only after confirming their address
        if user_email and instance.email_verified:
            # print('New user signal fired ...')
            send_welcome_email_task(user_email, user_email, instance.language)
            # send_welcome_email_task.delay(user_email, user_email, instance.language)

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
            send_amount_to_pay_email_task(instance.user.email, instance.amount_to_pay, instance.language)