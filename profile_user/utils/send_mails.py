from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings

def send_welcome_email(user_email, user_name):
    if user_name.find('@'):
        user_name = user_email.split("@")[0]
    subject = 'Welcome to IsAlgo comunity!'
    html_content = render_to_string('emails/welcome_email.html', {'user_name': user_name})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending welcome email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def new_member_email(user_email):
    subject = 'Welcome to Our Community!'
    html_content = render_to_string('emails/new_member.html')
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending new member email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def new_lifetime_email(user_email):
    subject = 'Welcome to Lifetime Membership!'
    html_content = render_to_string('emails/new_lifetime.html')
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending new lifetime email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def cancel_membership_email(user_email):
    subject = "We're Sorry to See You Go"
    html_content = render_to_string('emails/cancel_membership.html')
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending cancel member email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def access_removed_email(user_email):
    subject = "Unfortunately, your access has been removed."
    html_content = render_to_string('emails/access_removed.html')
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending remove access email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def overdue_access_removed_email(user_email):
    subject = "Action Required: Update Your Payment Method to Restore Access."
    html_content = render_to_string('emails/overdue_access_removed.html')
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending overdue remove access email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def new_strategy_mail(user_email, strategy_name, strategy_url, strategy_tv_url, strategy_img):
    subject = 'Check this one out!'
    html_content = render_to_string('emails/new_strategy.html', {'strategy_name': strategy_name, 'strategy_url': strategy_url, 'strategy_img': strategy_img, 'strategy_tv_url': strategy_tv_url})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def broker_account_added(user_email, account):
    account_name = account.name if account else "your broker account"
    subject = 'Broker Account Added!'
    html_content = render_to_string('emails/broker_added.html', {'account_name': account_name})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def broker_account_access_removed(user_email, account):
    account_name = account.name if account else "your broker account"
    subject = 'Broker Account Subscription Issue!'
    html_content = render_to_string('emails/broker_access_removed.html', {'account_name': account_name})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def broker_account_deleted(user_email, account=None):
    account_name = account.name if account else "your broker account"
    subject = 'Broker Account Deleted!'
    html_content = render_to_string('emails/broker_deleted.html', {})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def broker_account_overdue(user_email, account):
    account_name = account.name if account else "your broker account"
    subject = 'Broker Account Subscription Overdue!'
    html_content = render_to_string('emails/broker_overdue.html', {'account_name': account_name})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_gained(user_email, strategy, strategy_url):
    subject = 'You have a new subscriber!'
    html_content = render_to_string('emails/strategy_access_gained.html', {'strategy_name': strategy.name, 'strategy_url': strategy_url})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_removed(user_email, strategy, strategy_url):
    subject = 'You lost a subscriber!'
    html_content = render_to_string('emails/strategy_access_removed.html', {'strategy_name': strategy.name, 'strategy_url': strategy_url})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_overdue(user_email, strategy, strategy_url):
    subject = 'Strategy Subscription Overdue!'
    html_content = render_to_string('emails/strategy_access_past_due.html', {'strategy_name': strategy.name, 'strategy_url': strategy_url})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

