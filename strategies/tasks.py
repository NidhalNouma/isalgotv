from django.template.loader import render_to_string
from celery import shared_task
from django.core.mail import EmailMessage
from .models import User

from django.conf import settings

@shared_task
def send_strategy_email_to_all_users(strategy_name, strategy_url, strategy_tv_url, strategy_img):
    subject = 'Check this one out!'
    from_email = f"New strategy added! <{settings.EMAIL_HOST_USER}>"
    print("Sending new strategy mail to all users ... ", strategy_name)
    users = User.objects.all()
    
    for user in users:
        html_content = render_to_string('emails/new_strategy.html', {
            'strategy_name': strategy_name,
            'strategy_url': strategy_url,
            'strategy_img': strategy_img,
            'strategy_tv_url': strategy_tv_url
        })
        email = EmailMessage(subject, html_content, from_email, to=[user.email])
        email.content_subtype = 'html'
        email.send()
