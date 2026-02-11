"""
Django management command to send a test email using any email template.

Usage:
    python manage.py send_email user@example.com welcome_email
    python manage.py send_email user@example.com new_member
    python manage.py send_email user@example.com broker_added --params account_name="My Binance"
    python manage.py send_email user@example.com new_strategy --params strategy_name="RSI Pro" strategy_url="https://isalgo.com/s/1" strategy_type="Premium"
    python manage.py send_email user@example.com welcome_email --subject "Custom Subject"
    python manage.py send_email user@example.com broker_added --params account_name="Test" --list-params
"""
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings

from profile_user.utils.send_mails import email_context


# Template registry: template_name -> { subject, params }
TEMPLATES = {
    'welcome_email': {
        'subject': 'Welcome to IsAlgo community!',
        'params': ['username'],
    },
    'new_member': {
        'subject': 'Membership Confirmed - IsAlgo',
        'params': [],
    },
    'new_lifetime': {
        'subject': 'Lifetime Access Granted - IsAlgo',
        'params': [],
    },
    'cancel_membership': {
        'subject': 'Membership Canceled - IsAlgo',
        'params': [],
    },
    'access_removed': {
        'subject': 'Membership Access Removed - IsAlgo',
        'params': [],
    },
    'overdue_membership': {
        'subject': 'Payment Issue - IsAlgo',
        'params': [],
    },
    'new_strategy': {
        'subject': 'New Strategy Published - IsAlgo',
        'params': ['strategy_name', 'strategy_url', 'strategy_img', 'strategy_tv_url', 'strategy_type'],
    },
    'broker_added': {
        'subject': 'Account Connected - IsAlgo',
        'params': ['account_name'],
    },
    'broker_deleted': {
        'subject': 'Account Removed - IsAlgo',
        'params': ['account_name'],
    },
    'broker_access_removed': {
        'subject': 'Account Access Issue - IsAlgo',
        'params': ['account_name'],
    },
    'broker_overdue': {
        'subject': 'Account Payment Overdue - IsAlgo',
        'params': ['account_name'],
    },
    'strategy_access_gained': {
        'subject': 'Strategy Access Granted - IsAlgo',
        'params': ['strategy_name', 'strategy_url'],
    },
    'strategy_access_removed': {
        'subject': 'Strategy Access Suspended - IsAlgo',
        'params': ['strategy_name', 'strategy_url'],
    },
    'strategy_access_overdue': {
        'subject': 'Strategy Payment Overdue - IsAlgo',
        'params': ['strategy_name', 'strategy_url'],
    },
    'strategy_access_canceled': {
        'subject': 'Strategy Access Canceled - IsAlgo',
        'params': ['strategy_name', 'strategy_url'],
    },
    'complete_seller_account': {
        'subject': 'Complete Your Seller Account - IsAlgo',
        'params': [],
    },
    'seller_account_verified': {
        'subject': 'Seller Account Verified - IsAlgo',
        'params': [],
    },
    'amount_to_pay': {
        'subject': 'Outstanding Balance - IsAlgo',
        'params': ['amount'],
    },
    'amount_paid': {
        'subject': 'Payment Received - IsAlgo',
        'params': ['amount'],
    },
}


class Command(BaseCommand):
    help = 'Send a test email using any email template with custom parameters.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email address.')
        parser.add_argument('template', type=str, help=f'Template name (without .html). Available: {", ".join(TEMPLATES.keys())}')
        parser.add_argument('--subject', type=str, help='Custom email subject (overrides the default).')
        parser.add_argument(
            '--params',
            nargs='*',
            metavar='key=value',
            default=[],
            help='Template parameters as key=value pairs. E.g. --params account_name="My Account" strategy_type="Premium"',
        )
        parser.add_argument('--list-params', action='store_true', help='List expected parameters for the template and exit.')

    def handle(self, *args, **options):
        email_addr = options['email']
        template_name = options['template']

        # Validate template
        if template_name not in TEMPLATES:
            available = '\n  '.join(f'- {name}  (params: {", ".join(t["params"]) or "none"})' for name, t in TEMPLATES.items())
            raise CommandError(
                f'Unknown template "{template_name}". Available templates:\n  {available}'
            )

        template_info = TEMPLATES[template_name]

        # List params mode
        if options['list_params']:
            params = template_info['params']
            if params:
                self.stdout.write(f'Template "{template_name}" expects these parameters:')
                for p in params:
                    self.stdout.write(f'  - {p}')
            else:
                self.stdout.write(f'Template "{template_name}" has no extra parameters.')
            self.stdout.write(f'\nDefault subject: {template_info["subject"]}')
            return

        # Parse key=value params
        extra_params = {}
        for param in options['params']:
            if '=' not in param:
                raise CommandError(f'Invalid parameter format: "{param}". Use key=value format.')
            key, value = param.split('=', 1)
            extra_params[key.strip()] = value.strip()

        # Build context
        context = {**email_context(), **extra_params}

        # Render template
        template_path = f'emails/{template_name}.html'
        try:
            html_content = render_to_string(template_path, context=context)
        except Exception as e:
            raise CommandError(f'Failed to render template "{template_path}": {e}')

        # Send email
        subject = options['subject'] or template_info['subject']
        from_email = f"IsAlgo <{settings.EMAIL_HOST_USER}>"

        email = EmailMessage(subject, html_content, from_email=from_email, to=[email_addr])
        email.content_subtype = 'html'

        try:
            self.stdout.write(f'Sending "{template_name}" email to {email_addr}...')
            email.send()
            self.stdout.write(self.style.SUCCESS(f'Email sent successfully to {email_addr}'))
        except Exception as e:
            raise CommandError(f'Failed to send email: {e}')
