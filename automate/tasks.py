from django.template.loader import render_to_string
from celery import shared_task
from django.core.mail import EmailMessage

from profile_user.utils.send_mails import *

@shared_task
def send_broker_account_access_removed_task(user_email, account_name):
    broker_account_access_removed(user_email, account_name)

@shared_task
def send_broker_account_deleted_task(user_email):
    broker_account_deleted(user_email)
