from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User_Profile

from .tasks import send_welcome_email_task

@receiver(post_save, sender=User_Profile)
def user_profile_save(sender, instance, created, **kwargs):
    if created:
        # Send Emails to all users about the new added
        user_email = instance.user.email
        if user_email:
            send_welcome_email_task(user_email, user_email)
            # send_welcome_email_task.delay(user_email, user_email)
