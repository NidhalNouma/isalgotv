from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Strategy

@receiver(post_save, sender=Strategy)
def strategy_post_save(sender, instance, created, **kwargs):
    if created:
        # Send Emails to all users about the new added strategy
        pass
