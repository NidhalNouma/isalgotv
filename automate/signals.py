from django.db.models.signals import post_save
from django.dispatch import receiver
from automate.models import *
from automate.functions.performance import apply_trade_to_performance

@receiver(post_save, sender=TradeDetails)
def update_account_statistics_on_trade_save(sender, instance, created, **kwargs):
    if instance.status == "C":
        apply_trade_to_performance(instance)


