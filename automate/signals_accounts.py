from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from automate.models import (
    CryptoBrokerAccount,
    ForexBrokerAccount,
    AccountPerformance,
)

@receiver(post_save, sender=CryptoBrokerAccount)
def create_crypto_account_performance(sender, instance, created, **kwargs):
    if not created:
        return

    AccountPerformance.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.id,
    )


@receiver(post_save, sender=ForexBrokerAccount)
def create_forex_account_performance(sender, instance, created, **kwargs):
    if not created:
        return

    AccountPerformance.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.id,
    )