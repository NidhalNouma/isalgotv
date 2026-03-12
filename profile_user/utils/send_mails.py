from django.template.loader import render_to_string
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from django.utils.translation import gettext as _, override

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
    light_icons_url = f'{static_url}images/emails/icons-light/'

    social_urls = {
        'tv': 'https://www.tradingview.com/u/IsAlgo//?aff_id=134591&aff_sub=134591&source=134591',
        'discord': 'https://discord.gg/wVsXdGSMFg',
        'youtube': 'https://www.youtube.com/channel/UCE-MRbybrU5KobUTH1NRxRA',
        'instagram': 'https://www.instagram.com/isalgotrade/',
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
        'light_icons_url': light_icons_url,
        'support_email': settings.EMAIL_HOST_USER,
        'social_urls': social_urls,
    }


def send_marketing_email(recipients, subject, sections, preheader='', language='en'):
    """
    Send a marketing email built from an array of section objects.

    Args:
        recipients: email address (str) or list of email addresses
        subject: email subject line
        sections: list of dicts, each representing a section:
            {
                'title':          str  (optional),
                'description':    str  (optional, supports HTML),
                'align':          str  (optional, 'left'|'center', default 'left'),
                'image_position': str  (optional, 'before'|'after', default 'after'),
                'images_per_row': str  (optional, '1'|'2'|'3', default '1'),
                'images':         list (optional, list of {'src': str, 'alt': str, 'link': str}),
                'image_rows':     list (auto-generated, chunked images per row),
                'image_col_width':str  (auto-generated, % width per image column),
                'cta_text':       str  (optional, button label),
                'cta_url':        str  (optional, button URL),
                'cta_bg':         str  (optional, button background color, default '#3861f6'),
                'cta_color':      str  (optional, button text color, default '#ffffff'),
                'divider':        bool (optional, show divider after section, default True),
            }
        preheader: preview text shown in inbox (optional)
    """
    if isinstance(recipients, str):
        recipients = [recipients]

    context = {
        'sections': sections,
        'email_subject': subject,
        'preheader': preheader,
        'language': language,
        **email_context(),
    }
    html_content = render_to_string('emails/marketing_email.html', context=context)
    from_email = f"IsAlgo <{settings.EMAIL_HOST_USER}>"

    messages = []
    for recipient in recipients:
        msg = EmailMessage(subject, html_content, from_email=from_email, to=[recipient])
        msg.content_subtype = 'html'
        messages.append(msg)

    try:
        connection = get_connection()
        sent = connection.send_messages(messages)
        print(f'Marketing email sent to {sent}/{len(recipients)} recipient(s)')
    except Exception as e:
        print(f"Error sending marketing emails: {e}")


def send_welcome_email(user_email, username, language='en'):
    if username.find('@'):
        username = user_email.split("@")[0]
    with override(language):
        subject = _('Welcome to IsAlgo community!')
        html_content = render_to_string('emails/welcome_email.html', context={'username': username, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending welcome email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def new_member_email(user_email, language='en'):
    with override(language):
        subject = _('Welcome to Our Community!')
        html_content = render_to_string('emails/new_member.html', context={'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending new member email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def new_lifetime_email(user_email, language='en'):
    with override(language):
        subject = _('Welcome to Lifetime Membership!')
        html_content = render_to_string('emails/new_lifetime.html', context={'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending new lifetime email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def cancel_membership_email(user_email, language='en'):
    with override(language):
        subject = _("We're Sorry to See You Go")
        html_content = render_to_string('emails/cancel_membership.html', context={'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending cancel member email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def access_removed_email(user_email, language='en'):
    with override(language):
        subject = _("Unfortunately, your access has been removed.")
        html_content = render_to_string('emails/access_removed.html', context={'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending remove access email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def overdue_access_removed_email(user_email, language='en'):
    with override(language):
        subject = _("Action Required: Update Your Payment Method to Restore Access.")
        html_content = render_to_string('emails/overdue_membership.html', context={'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending overdue remove access email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def new_strategy_mail(user_email, strategy_name, strategy_url, strategy_tv_url, strategy_img, strategy_type='Premium', language='en'):
    with override(language):
        subject = _('Check this one out!')
        html_content = render_to_string('emails/new_strategy.html', context={'strategy_name': strategy_name, 'strategy_url': strategy_url, 'strategy_img': strategy_img, 'strategy_tv_url': strategy_tv_url, 'strategy_type': strategy_type, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def broker_account_added(user_email, account, language='en'):
    with override(language):
        account_name = account.name if account else _("your broker account")
        subject = _('Account connected: %(account_name)s!') % {'account_name': account_name}
        html_content = render_to_string('emails/broker_added.html', context={'account_name': account_name, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def broker_account_access_removed(user_email, account, language='en'):
    with override(language):
        account_name = account.name if account else _("your broker account")
        subject = _('Access Removed: %(account_name)s!') % {'account_name': account_name}
        html_content = render_to_string('emails/broker_access_removed.html', context={'account_name': account_name, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def broker_account_deleted(user_email, account=None, language='en'):
    with override(language):
        account_name = account.name if account else _("your broker account")
        subject = _('Broker Account Deleted: %(account_name)s!') % {'account_name': account_name}
        html_content = render_to_string('emails/broker_deleted.html', context={'account_name': account_name, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def broker_account_overdue(user_email, account, language='en'):
    with override(language):
        account_name = account.name if account else _("your broker account")
        subject = _('Broker Account Subscription Overdue: %(account_name)s!') % {'account_name': account_name}
        html_content = render_to_string('emails/broker_overdue.html', context={'account_name': account_name, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def automate_log_error(user_email, account_name, alert_message, error_message, language='en'):
    with override(language):
        subject = _('Automation Error: %(account_name)s') % {'account_name': account_name}
        html_content = render_to_string('emails/automate_log_error.html', context={
            'account_name': account_name,
            'alert_message': alert_message,
            'error_message': error_message,
            'language': language,
            **email_context()
        })
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'

    try:
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")

def strategy_access_gained(user_email, strategy, language='en'):
    with override(language):
        subject = _('Access Granted: You now have access to %(strategy_name)s!') % {'strategy_name': strategy.name}
        e_context = email_context()
        strategy_url = f"{e_context['strategies_url']}{strategy.slug}/"
        html_content = render_to_string('emails/strategy_access_gained.html', context={'strategy_name': strategy.name, 'strategy_url': strategy_url, 'language': language, **e_context})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_removed(user_email, strategy, language='en'):
    with override(language):
        subject = _('You lost your %(strategy_name)s access!') % {'strategy_name': strategy.name}
        e_context = email_context()
        strategy_url = f"{e_context['strategies_url']}{strategy.slug}/"
        html_content = render_to_string('emails/strategy_access_removed.html', context={'strategy_name': strategy.name, 'strategy_url': strategy_url, 'language': language, **e_context})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_overdue(user_email, strategy, language='en'):
    with override(language):
        subject = _('Strategy Subscription Overdue: %(strategy_name)s') % {'strategy_name': strategy.name}
        e_context = email_context()
        strategy_url = f"{e_context['strategies_url']}{strategy.slug}/"
        html_content = render_to_string('emails/strategy_access_overdue.html', context={'strategy_name': strategy.name, 'strategy_url': strategy_url, 'language': language, **e_context})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def strategy_access_canceled(user_email, strategy, language='en'):
    with override(language):
        subject = _('Your access to %(strategy_name)s has been canceled') % {'strategy_name': strategy.name}
        e_context = email_context()
        strategy_url = f"{e_context['strategies_url']}{strategy.slug}/"
        html_content = render_to_string('emails/strategy_access_canceled.html', context={'strategy_name': strategy.name, 'strategy_url': strategy_url, 'language': language, **e_context})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def complete_seller_account(user_email, language='en'):
    with override(language):
        subject = _('Complete Your Seller Account Setup')
        html_content = render_to_string('emails/complete_seller_account.html', context={'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending complete seller account email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def seller_account_verified(user_email, language='en'):
    with override(language):
        subject = _('Your Seller Account is Verified!')
        html_content = render_to_string('emails/seller_account_verified.html', context={'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending seller account verified email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def seller_first_subscriber_to_strategy(user_email, strategy, language='en'):
    strategy_name = strategy.name
    strategy_url = f"https://www.isalgo.com/strategies/{strategy.slug}/"
    price = strategy.price.amount
    interval = strategy.price.interval
    interval_count = strategy.price.interval_count
    with override(language):
        subject = _('Congratulations on Your First Subscriber for %(strategy_name)s!') % {'strategy_name': strategy_name}
        html_content = render_to_string('emails/first_subscriber.html', context={'strategy_name': strategy_name, 'strategy_url': strategy_url, 'price': price, 'interval': interval, 'interval_count': interval_count, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending first subscriber email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def seller_ten_subscribers_to_strategy(user_email, strategy, language='en'):
    strategy_name = strategy.name
    strategy_url = f"https://www.isalgo.com/strategies/{strategy.slug}/"
    price = strategy.price.amount
    interval = strategy.price.interval
    interval_count = strategy.price.interval_count
    with override(language):
        subject = _('%(strategy_name)s Just Hit 10 Subscribers!') % {'strategy_name': strategy_name}
        html_content = render_to_string('emails/ten_subscribers.html', context={'strategy_name': strategy_name, 'strategy_url': strategy_url, 'price': price, 'interval': interval, 'interval_count': interval_count, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'

    try:
        print('Sending 10 subscribers email', user_email)
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")

def seller_hundred_subscribers_to_strategy(user_email, strategy, language='en'):
    strategy_name = strategy.name
    strategy_url = f"https://www.isalgo.com/strategies/{strategy.slug}/"
    price = strategy.price.amount
    interval = strategy.price.interval
    interval_count = strategy.price.interval_count
    with override(language):
        subject = _('Incredible — %(strategy_name)s Just Hit 100 Subscribers!') % {'strategy_name': strategy_name}
        html_content = render_to_string('emails/hundred_subscribers.html', context={'strategy_name': strategy_name, 'strategy_url': strategy_url, 'price': price, 'interval': interval, 'interval_count': interval_count, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'

    try:
        print('Sending 100 subscribers email', user_email)
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")

def seller_hundred_thousand_subscribers_to_strategy(user_email, strategy, language='en'):
    strategy_name = strategy.name
    strategy_url = f"https://www.isalgo.com/strategies/{strategy.slug}/"
    price = strategy.price.amount
    interval = strategy.price.interval
    interval_count = strategy.price.interval_count
    with override(language):
        subject = _('%(strategy_name)s Just Hit 100,000 Subscribers!') % {'strategy_name': strategy_name}
        html_content = render_to_string('emails/hundred_thousand_subscribers.html', context={'strategy_name': strategy_name, 'strategy_url': strategy_url, 'price': price, 'interval': interval, 'interval_count': interval_count, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'

    try:
        print('Sending 100K subscribers email', user_email)
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")

def seller_million_subscribers_to_strategy(user_email, strategy, language='en'):
    strategy_name = strategy.name
    strategy_url = f"https://www.isalgo.com/strategies/{strategy.slug}/"
    price = strategy.price.amount
    interval = strategy.price.interval
    interval_count = strategy.price.interval_count
    with override(language):
        subject = _('Legendary — %(strategy_name)s Just Hit 1,000,000 Subscribers!') % {'strategy_name': strategy_name}
        html_content = render_to_string('emails/million_subscribers.html', context={'strategy_name': strategy_name, 'strategy_url': strategy_url, 'price': price, 'interval': interval, 'interval_count': interval_count, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'

    try:
        print('Sending 1M subscribers email', user_email)
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")

def amount_to_pay_email(user_email, amount, language='en'):
    with override(language):
        subject = _('Outstanding Balance on Your IsAlgo Account')
        html_content = render_to_string('emails/amount_to_pay.html', context={'amount': amount, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending amount to pay email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def amount_paid_email(user_email, amount, language='en'):
    with override(language):
        subject = _('Payment Received - Thank You!')
        html_content = render_to_string('emails/amount_paid.html', context={'amount': amount, 'language': language, **email_context()})
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[user_email])
    email.content_subtype = 'html'  # This is required because default is plain text
    
    try:
        print('Sending amount paid email', user_email)
        email.send()
    except Exception as e:
        # Handle the exception as needed
        print(f"Error sending email: {e}")

def new_report_added(owner_email, strategy_name, strategy_url, author_name, pair, time_frame_int, time_frame, broker, language='en'):
    with override(language):
        subject = _('New Report on %(strategy_name)s') % {'strategy_name': strategy_name}
        html_content = render_to_string('emails/new_report.html', context={
            'strategy_name': strategy_name,
            'strategy_url': strategy_url,
            'author_name': author_name,
            'pair': pair,
            'time_frame_int': time_frame_int,
            'time_frame': time_frame,
            'broker': broker,
            'language': language,
            **email_context()
        })
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[owner_email])
    email.content_subtype = 'html'

    try:
        print('Sending new report email', owner_email)
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")

def new_comment_added(owner_email, strategy_name, strategy_url, author_name, comment_preview):
    subject = _('New Comment on %(strategy_name)s') % {'strategy_name': strategy_name}
    html_content = render_to_string('emails/new_comment.html', context={
        'strategy_name': strategy_name,
        'strategy_url': strategy_url,
        'author_name': author_name,
        'comment_preview': comment_preview,
        **email_context()
    })
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=[owner_email])
    email.content_subtype = 'html'

    try:
        print('Sending new comment email', owner_email)
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")

def new_reply_on_report(recipient_emails, strategy_name, strategy_url, author_name, reply_preview):
    subject = _('New Reply on Report — %(strategy_name)s') % {'strategy_name': strategy_name}
    html_content = render_to_string('emails/new_reply_on_report.html', context={
        'strategy_name': strategy_name,
        'strategy_url': strategy_url,
        'author_name': author_name,
        'reply_preview': reply_preview,
        **email_context()
    })
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=recipient_emails)
    email.content_subtype = 'html'

    try:
        print('Sending new reply on report email', recipient_emails)
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")

def new_reply_on_comment(recipient_emails, strategy_name, strategy_url, author_name, reply_preview):
    subject = _('New Reply on Comment — %(strategy_name)s') % {'strategy_name': strategy_name}
    html_content = render_to_string('emails/new_reply_on_comment.html', context={
        'strategy_name': strategy_name,
        'strategy_url': strategy_url,
        'author_name': author_name,
        'reply_preview': reply_preview,
        **email_context()
    })
    email = EmailMessage(subject, html_content, from_email=f"IsAlgo <{settings.EMAIL_HOST_USER}>", to=recipient_emails)
    email.content_subtype = 'html'

    try:
        print('Sending new reply on comment email', recipient_emails)
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")