"""
Django management command to send ALL available email templates at once with dummy data.
Useful for visually testing every email template in one go.

Usage:
    DJANGO_SETTINGS_MODULE=main_app.settings.dev python manage.py send_all_emails user@example.com
    DJANGO_SETTINGS_MODULE=main_app.settings.dev python manage.py send_all_emails user@example.com --delay 3
    DJANGO_SETTINGS_MODULE=main_app.settings.dev python manage.py send_all_emails user@example.com --only new_strategy,broker_added
    DJANGO_SETTINGS_MODULE=main_app.settings.dev python manage.py send_all_emails user@example.com --exclude welcome_email
"""
import time

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings

from profile_user.utils.send_mails import email_context
from profile_user.management.commands.send_email import TEMPLATES


# Dummy params for each template
DUMMY_PARAMS = {
    'welcome_email': {
        'username': 'JohnTrader',
    },
    'new_member': {},
    'new_lifetime': {},
    'cancel_membership': {},
    'access_removed': {},
    'overdue_membership': {},
    'new_strategy': {
        'strategy_name': 'RSI Momentum Pro',
        'strategy_url': 'https://www.isalgo.com/strategies/',
        'strategy_img': 'https://www.isalgo.com/static/images/logo-naked.png',
        'strategy_tv_url': 'https://www.tradingview.com/',
        'strategy_type': 'Premium',
    },
    'broker_added': {
        'account_name': 'My Binance Futures',
    },
    'broker_deleted': {
        'account_name': 'Old MetaTrader 5',
    },
    'broker_access_removed': {
        'account_name': 'Alpaca Paper Trading',
    },
    'broker_overdue': {
        'account_name': 'Interactive Brokers',
    },
    'strategy_access_gained': {
        'strategy_name': 'MACD Scalper v2',
        'strategy_url': 'https://www.isalgo.com/strategies/',
    },
    'strategy_access_removed': {
        'strategy_name': 'Bollinger Breakout',
        'strategy_url': 'https://www.isalgo.com/strategies/',
    },
    'strategy_access_overdue': {
        'strategy_name': 'EMA Crossover Plus',
        'strategy_url': 'https://www.isalgo.com/strategies/',
    },
    'strategy_access_canceled': {
        'strategy_name': 'Volume Profile Elite',
        'strategy_url': 'https://www.isalgo.com/strategies/',
    },
    'complete_seller_account': {},
    'seller_account_verified': {},
}


class Command(BaseCommand):
    help = 'Send ALL email templates with dummy data to a single recipient for testing.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email address.')
        parser.add_argument(
            '--delay',
            type=int,
            default=2,
            help='Delay in seconds between each email (default: 2). Helps avoid rate limits.',
        )
        parser.add_argument(
            '--only',
            type=str,
            default='',
            help='Comma-separated list of template names to send. E.g. --only new_strategy,broker_added',
        )
        parser.add_argument(
            '--exclude',
            type=str,
            default='',
            help='Comma-separated list of template names to skip. E.g. --exclude welcome_email,new_member',
        )

    def handle(self, *args, **options):
        email_addr = options['email']
        delay = options['delay']

        # Determine which templates to send
        if options['only']:
            template_names = [t.strip() for t in options['only'].split(',')]
            for name in template_names:
                if name not in TEMPLATES:
                    raise CommandError(f'Unknown template "{name}". Available: {", ".join(TEMPLATES.keys())}')
        else:
            template_names = list(TEMPLATES.keys())

        if options['exclude']:
            excluded = {t.strip() for t in options['exclude'].split(',')}
            template_names = [t for t in template_names if t not in excluded]

        total = len(template_names)
        self.stdout.write(f'\nSending {total} email templates to {email_addr}')
        self.stdout.write(f'Delay between emails: {delay}s\n')

        success_count = 0
        fail_count = 0
        base_context = email_context()
        from_email = f"IsAlgo <{settings.EMAIL_HOST_USER}>"

        for i, template_name in enumerate(template_names, 1):
            template_info = TEMPLATES[template_name]
            dummy = DUMMY_PARAMS.get(template_name, {})

            context = {**base_context, **dummy}
            subject = f'[{i}/{total}] {template_info["subject"]}'
            template_path = f'emails/{template_name}.html'

            try:
                html_content = render_to_string(template_path, context=context)
                email = EmailMessage(subject, html_content, from_email=from_email, to=[email_addr])
                email.content_subtype = 'html'
                email.send()

                self.stdout.write(self.style.SUCCESS(f'  [{i}/{total}] ✓ {template_name}'))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [{i}/{total}] ✗ {template_name}: {e}'))
                fail_count += 1

            # Delay between sends (skip after last one)
            if i < total and delay > 0:
                time.sleep(delay)

        # Summary
        self.stdout.write('')
        self.stdout.write(f'Done! {success_count} sent, {fail_count} failed out of {total} templates.')
        if success_count == total:
            self.stdout.write(self.style.SUCCESS('All emails sent successfully! Check your inbox.'))
