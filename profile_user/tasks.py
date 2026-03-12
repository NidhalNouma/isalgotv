from django.template.loader import render_to_string
from celery import shared_task
from django.core.mail import EmailMessage

from .utils.send_mails import *

@shared_task
def send_welcome_email_task(user_email, user_name, language='en'):
    send_welcome_email(user_email, user_name, language)

@shared_task
def send_new_member_email_task(user_email, language='en'):
    new_member_email(user_email, language)

@shared_task
def send_new_lifetime_email_task(user_email, language='en'):
    new_lifetime_email(user_email, language)

@shared_task
def send_cancel_membership_email_task(user_email, language='en'):
    cancel_membership_email(user_email, language)

@shared_task
def access_removed_email_task(user_email, language='en'):
    access_removed_email(user_email, language)

@shared_task
def overdue_access_removed_email_task(user_email, language='en'):
    overdue_access_removed_email(user_email, language)

@shared_task
def send_complete_seller_account_email_task(user_email, language='en'):
    complete_seller_account(user_email, language)

@shared_task
def send_seller_account_verified_email_task(user_email, language='en'):
    seller_account_verified(user_email, language)

@shared_task
def send_amount_to_pay_email_task(user_email, amount, language='en'):
    amount_to_pay_email(user_email, amount, language)

@shared_task
def send_amount_paid_email_task(user_email, amount, language='en'):
    amount_paid_email(user_email, amount, language)