from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Strategy, StrategySubscriber
from django.contrib.auth.models import User

from .tasks import send_strategy_email_to_all_users, send_strategy_first_subscriber_email_task, send_strategy_ten_subscribers_email_task, send_strategy_hundred_subscribers_email_task, send_strategy_hundred_thousand_subscribers_email_task, send_strategy_million_subscribers_email_task

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


@receiver(post_save, sender=StrategySubscriber)
def notify_subscriber_milestone(sender, instance, created, **kwargs):
    if created:
        strategy = instance.strategy
        seller_email = strategy.created_by.email

        # Count active subscribers for the strategy
        active_subscribers_count = StrategySubscriber.objects.filter(strategy=strategy, subscription_id__isnull=False, active=True).count()

        if active_subscribers_count == 1:
            print(f"First subscriber for strategy '{strategy.name}' detected. Sending email to seller {seller_email} ...")
            send_strategy_first_subscriber_email_task(seller_email, strategy.id)
        elif active_subscribers_count == 10:
            print(f"10 subscribers for strategy '{strategy.name}' reached. Sending email to seller {seller_email} ...")
            send_strategy_ten_subscribers_email_task(seller_email, strategy.id)
        elif active_subscribers_count == 100:
            print(f"100 subscribers for strategy '{strategy.name}' reached. Sending email to seller {seller_email} ...")
            send_strategy_hundred_subscribers_email_task(seller_email, strategy.id)
        elif active_subscribers_count == 100_000:
            print(f"100K subscribers for strategy '{strategy.name}' reached. Sending email to seller {seller_email} ...")
            send_strategy_hundred_thousand_subscribers_email_task(seller_email, strategy.id)
        elif active_subscribers_count == 1_000_000:
            print(f"1M subscribers for strategy '{strategy.name}' reached. Sending email to seller {seller_email} ...")
            send_strategy_million_subscribers_email_task(seller_email, strategy.id)
    


