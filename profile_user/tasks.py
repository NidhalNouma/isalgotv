from django.template.loader import render_to_string
from celery import shared_task
from django.core.mail import EmailMessage

from .utils.send_mails import *

@shared_task
def send_welcome_email_task(user_email, user_name):
    send_welcome_email(user_email, user_name)