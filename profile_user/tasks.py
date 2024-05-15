from django.template.loader import render_to_string
from celery import shared_task
from django.core.mail import EmailMessage

from .utils.send_mails import *

@shared_task
def send_welcome_email_task(user_email, user_name):
    send_welcome_email(user_email, user_name)


@shared_task
def send_new_member_email_task(user_email):
    new_member_email(user_email)

@shared_task
def send_new_lifetime_email_task(user_email):
    new_lifetime_email(user_email)

@shared_task
def send_cancel_membership_email_task(user_email):
    cancel_membership_email(user_email)