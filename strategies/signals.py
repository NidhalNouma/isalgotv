from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Strategy, StrategySubscriber, StrategyResults, StrategyComments, Replies
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from .tasks import (
    send_strategy_email_to_all_users,
    send_strategy_first_subscriber_email_task,
    send_strategy_ten_subscribers_email_task,
    send_strategy_hundred_subscribers_email_task,
    send_strategy_hundred_thousand_subscribers_email_task,
    send_strategy_million_subscribers_email_task,
    send_new_report_email_task,
    send_new_comment_email_task,
    send_new_reply_on_report_email_task,
    send_new_reply_on_comment_email_task,
)

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
    


@receiver(post_save, sender=StrategyResults)
def notify_new_report(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        strategy = instance.strategy
        owner_email = strategy.created_by.email
        author_email = instance.created_by.user.email

        # Don't notify the owner if they created the report themselves
        if owner_email == author_email:
            return

        strategy_url = f"https://www.isalgo.com/strategies/{strategy.slug}/?report={instance.id}"
        author_name = instance.created_by.tradingview_username or 'Anonymous'

        send_new_report_email_task(
            owner_email,
            strategy.name,
            strategy_url,
            author_name,
            instance.pair,
            instance.time_frame_int,
            instance.time_frame,
            instance.broker,
        )
    except Exception as e:
        print(f" Error sending new report email: {e}")


@receiver(post_save, sender=StrategyComments)
def notify_new_comment(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        strategy = instance.strategy
        owner_email = strategy.created_by.email
        author_email = instance.created_by.user.email

        # Don't notify the owner if they wrote the comment themselves
        if owner_email == author_email:
            return

        strategy_url = f"https://www.isalgo.com/strategies/{strategy.slug}/?comment={instance.id}"
        author_name = instance.created_by.tradingview_username or 'Anonymous'
        comment_preview = instance.description[:200]

        send_new_comment_email_task(
            owner_email,
            strategy.name,
            strategy_url,
            author_name,
            comment_preview,
        )
    except Exception as e:
        print(f" Error sending new comment email: {e}")


def _get_root_and_strategy(reply):
    """Walk up GenericFK chain to find the root StrategyResults or StrategyComments."""
    current = reply.content_object
    while isinstance(current, Replies):
        current = current.content_object
    return current


def _collect_reply_emails(parent_obj, exclude_email):
    """Collect emails from the parent owner and all repliers, excluding the author."""
    emails = set()

    # Add the parent (report/comment) owner
    emails.add(parent_obj.created_by.user.email)

    # Add all repliers on this parent
    parent_ct = ContentType.objects.get_for_model(parent_obj)
    for reply in Replies.objects.filter(content_type=parent_ct, object_id=parent_obj.id).select_related('created_by__user'):
        emails.add(reply.created_by.user.email)

    # Remove the person who just replied
    emails.discard(exclude_email)
    return list(emails)


@receiver(post_save, sender=Replies)
def notify_new_reply(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        root = _get_root_and_strategy(instance)
        if root is None:
            return

        author_email = instance.created_by.user.email
        author_name = instance.created_by.tradingview_username or 'Anonymous'
        reply_preview = instance.description[:200]

        if isinstance(root, StrategyResults):
            strategy = root.strategy
            strategy_url = f"https://www.isalgo.com/strategies/{strategy.slug}/?report={root.id}"
            recipient_emails = _collect_reply_emails(root, author_email)

            if recipient_emails:
                send_new_reply_on_report_email_task(
                    recipient_emails,
                    strategy.name,
                    strategy_url,
                    author_name,
                    reply_preview,
                )
        elif isinstance(root, StrategyComments):
            strategy = root.strategy
            strategy_url = f"https://www.isalgo.com/strategies/{strategy.slug}/?comment={root.id}"
            recipient_emails = _collect_reply_emails(root, author_email)

            if recipient_emails:
                send_new_reply_on_comment_email_task(
                    recipient_emails,
                    strategy.name,
                    strategy_url,
                    author_name,
                    reply_preview,
                )
    except Exception as e:
        print(f" Error sending new reply email: {e}")