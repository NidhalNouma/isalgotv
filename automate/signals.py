from django.db.models.signals import post_save
from django.dispatch import receiver
from automate.models import *
from performance.functions.performance import apply_trade_to_performance
from automate.tasks import send_automate_log_error_task

@receiver(post_save, sender=TradeDetails)
def update_account_statistics_on_trade_save(sender, instance, created, **kwargs):
    try:
        if instance.status == "C":
            apply_trade_to_performance(instance)
    except Exception as e:
        print(f" Error applying trade to performance: {e}")


@receiver(post_save, sender=LogMessage)
def notify_automate_log_error(sender, instance, created, **kwargs):
    if not created or instance.response_status != "E":
        return

    try:
        broker_account = instance.content_object
        if broker_account is None:
            return

        user_profile = broker_account.created_by
        user_email = user_profile.user.email
        account_name = broker_account.name or "your broker account"

        send_automate_log_error_task(
            user_email,
            account_name,
            instance.alert_message,
            instance.response_message,
        )
    except Exception as e:
        print(f" Error sending automate log error email: {e}")
        


