from django.db.models.signals import post_save
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from profile_user.models import User_Profile

from profile_user.tasks import send_welcome_email_task


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
