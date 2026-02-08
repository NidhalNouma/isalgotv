from celery import shared_task
from profile_user.utils.send_mails import *

@shared_task
def send_broker_account_access_removed_task(user_email, account):
    broker_account_access_removed(user_email, account)

@shared_task
def send_broker_account_deleted_task(user_email, account=None):
    broker_account_deleted(user_email, account=account)

@shared_task
def send_broker_account_access_expiring_task(user_email, account):
    broker_account_overdue(user_email, account)