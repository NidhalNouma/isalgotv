from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings

def email_context():
    url = 'https://www.isalgo.com/'
    strategies_url = f'{url}strategies/'
    reports_url = f'{url}reports/'
    automate_url = f'{url}automate/'
    pricing_url = f'{url}my/membership/'
    docs_url = f'{url}docs/Introduction/'
    static_url = settings.STATIC_URL
    # logo_url = f'{static_url}images/logo-naked.png'
    icons_url = f'{static_url}images/emails/icons/'
    dark_icons_url = f'{static_url}images/emails/icons-dark/'

    social_urls = {
        'tv': 'https://www.tradingview.com/u/IsAlgo/',
        'discord': 'https://discord.gg/4Zz5X9jG',
        'youtube': 'https://www.youtube.com/@IsAlgo',
        'instagram': 'https://www.instagram.com/IsAlgo/',
    }

    return {
        'site_name': 'IsAlgo',
        'site_url': url,
        'strategies_url': strategies_url,
        'reports_url': reports_url,
        'automate_url': automate_url,
        'pricing_url': pricing_url,
        'docs_url': docs_url,
        'static_url': static_url,
        'icons_url': icons_url,
        'dark_icons_url': dark_icons_url,
        'support_email': settings.EMAIL_HOST_USER,
        'social_urls': social_urls,
    }


def send_welcome_email(user_email, username):
    if username.find('@'):
        username = user_email.split("@")[0]
    subject = 'Welcome to IsAlgo community!'
    html_content = render_to_string('emails/welcome_email.html', context={'username': username, **email_context()})
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
    html_content = render_to_string('emails/new_member.html', context={**email_context()})
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
    html_content = render_to_string('emails/new_lifetime.html', context={**email_context()})
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
    html_content = render_to_string('emails/cancel_membership.html', context={**email_context()})
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
    html_content = render_to_string('emails/access_removed.html', context={**email_context()})
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
    html_content = render_to_string('emails/overdue_membership.html', context={**email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending overdue remove access email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def new_strategy_mail(user_email, strategy_name, strategy_url, strategy_tv_url, strategy_img, strategy_type='Premium'):
    subject = 'Check this one out!'
    html_content = render_to_string('emails/new_strategy.html', context={'strategy_name': strategy_name, 'strategy_url': strategy_url, 'strategy_img': strategy_img, 'strategy_tv_url': strategy_tv_url, 'strategy_type': strategy_type, **email_context()})
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
    html_content = render_to_string('emails/broker_added.html', context={'account_name': account_name, **email_context()})
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
    html_content = render_to_string('emails/broker_access_removed.html', context={'account_name': account_name, **email_context()})
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
    html_content = render_to_string('emails/broker_deleted.html', context={'account_name': account_name, **email_context()})
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
    html_content = render_to_string('emails/broker_overdue.html', context={'account_name': account_name, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_gained(user_email, strategy):
    subject = 'You have a new subscriber!'
    e_context = email_context()
    strategy_url = f"{e_context['strategies_url']}{strategy.slug}/"
    html_content = render_to_string('emails/strategy_access_gained.html', context={'strategy_name': strategy.name, 'strategy_url': strategy_url, **e_context})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_removed(user_email, strategy):
    subject = 'You lost a subscriber!'
    e_context = email_context()
    strategy_url = f"{e_context['strategies_url']}{strategy.slug}/"
    html_content = render_to_string('emails/strategy_access_removed.html', context={'strategy_name': strategy.name, 'strategy_url': strategy_url, **e_context})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_overdue(user_email, strategy):
    subject = 'Strategy Subscription Overdue!'
    e_context = email_context()
    strategy_url = f"{e_context['strategies_url']}{strategy.slug}/"

    html_content = render_to_string('emails/strategy_access_overdue.html', context={'strategy_name': strategy.name, 'strategy_url': strategy_url, **e_context})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_canceled(user_email, strategy):
    subject = 'Strategy Subscription Canceled'
    e_context = email_context()
    strategy_url = f"{e_context['strategies_url']}{strategy.slug}/"

    html_content = render_to_string('emails/strategy_access_canceled.html', context={'strategy_name': strategy.name, 'strategy_url': strategy_url, **e_context})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

