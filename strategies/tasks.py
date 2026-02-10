from django.template.loader import render_to_string
from celery import shared_task
from django.core.mail import EmailMessage, get_connection

from django.conf import settings

from profile_user.utils.send_mails import strategy_access_canceled, strategy_access_overdue, strategy_access_removed, strategy_access_gained

@shared_task
def send_strategy_email_to_all_users(emails, strategy, header, subject, html_content):

    strategy_name = strategy.name
    strategy_url = 'https://www.isalgo.com/strategies/' + strategy.slug
    strategy_tv_url = strategy.tradingview_url
    strategy_img =  strategy.image_url

    print("Sending new strategy mail to all users ... ", strategy_name)

    if not subject:
        subject = 'Check this one out!'
    if header:
        from_email = f"IsAlgo - {header} <{settings.EMAIL_HOST_USER}>"
    else:
        from_email = f"IsAlgo - New strategy added! <{settings.EMAIL_HOST_USER}>"
    
    if not html_content:
        html_content = render_to_string('emails/new_strategy.html', {
            'strategy_name': strategy_name,
            'strategy_url': strategy_url,
            'strategy_img': strategy_img,
            'strategy_tv_url': strategy_tv_url,
            'strategy_type': strategy.premium, 
        })
    
    # Open one connection
    connection = get_connection()

    # Build all messages
    messages = []
    for recipient in emails:
        msg = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=from_email,
            to=[recipient],
            connection=connection
        )
        msg.content_subtype = "html"
        messages.append(msg)

    # Send them all in one go (over the same connection)
    connection.send_messages(messages)




@shared_task
def send_strategy_gained_email_task(user_email, strategy):
    strategy_access_gained(user_email, strategy)

@shared_task
def send_strategy_access_canceled_email_task(user_email, strategy):
    strategy_access_canceled(user_email, strategy)

@shared_task
def send_strategy_lost_email_task(user_email, strategy):
    strategy_access_removed(user_email, strategy)

@shared_task
def send_strategy_access_expiring_email_task(user_email, strategy):
    strategy_access_overdue(user_email, strategy)