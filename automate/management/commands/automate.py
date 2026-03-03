"""
Django management command to test the webhook alert workflow for an account.

Sends a sequence of test alerts (buy, partial close, full close, sell, partial close, full close)
to validate the full webhook pipeline.

Usage:
    python manage.py automate <webhook_id> --volume 0.01 --symbol EURUSD --delay 2
    python manage.py automate <webhook_id> --volume 0.001 --symbol BTCUSDT --delay 3
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import requests
import time


class Command(BaseCommand):
    help = "Test the webhook alert workflow for a trading account by sending a sequence of simulated alerts."

    def add_arguments(self, parser):
        parser.add_argument(
            'webhook_id',
            type=str,
            help='The account webhook custom ID'
        )
        parser.add_argument(
            '--volume',
            type=str,
            required=True,
            help='Trade volume (e.g., 0.01, 0.001)'
        )
        parser.add_argument(
            '--symbol',
            type=str,
            required=True,
            help='Trading symbol (e.g., EURUSD, BTCUSDT)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2,
            help='Delay in seconds between alerts (default: 2)'
        )
        parser.add_argument(
            '--broker-type',
            type=str,
            choices=['crypto', 'forex'],
            default=None,
            help='Broker type — auto-detected from the account if not provided'
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default=None,
            help='Override base webhook URL (default: https://webhook.isalgo.com)'
        )
        parser.add_argument(
            '--custom-id',
            type=str,
            default=None,
            help='Override custom ID for the webhook alerts'
        )
        parser.add_argument(
            '--actions',
            type=str,
            default='buy,xbuy:60,xbuy:100,sell,xsell:60,xsell:100',
            help='Comma-separated list of actions to test (default: buy,xbuy:60,xbuy:100,sell,xsell:60,xsell:100). '
                 'Use "buy" for entry, "xbuy:60" for 60%% close, "xbuy:100" for full close, '
                 '"sell" for sell entry, "xsell:60" for 60%% close, and "xsell:100" for full close.'
        )
        parser.add_argument(
            '--extra-commands',
            type=str,
            default='',
            help='Extra commands to include in the alert message, separated by space (e.g., "T=1 SL=1.2345 TP=1.3456")'
        )

    def handle(self, *args, **options):
        webhook_id = options['webhook_id']
        volume = options['volume']
        symbol = options['symbol']
        delay = options['delay']
        broker_type = options['broker_type']
        base_url = options['base_url']
        custom_id = options['custom_id']
        actions = options['actions'].split(',')
        extra_commands = options['extra_commands']

        # Auto-detect broker type from the account if not provided
        if not broker_type:
            broker_type = self._detect_broker_type(webhook_id)

        # Determine the webhook path prefix
        path_prefix = 'c' if broker_type == 'crypto' else 'f'

        # Build base URL
        if not base_url:
            parent_host = getattr(settings, 'PARENT_HOST', 'isalgo.com')
            scheme = 'http' if 'local' in parent_host or '127.0.0.1' in parent_host else 'https'
            base_url = f'{scheme}://webhook.{parent_host}'

        webhook_url = f'{base_url}/{path_prefix}/{webhook_id}'

        self.stdout.write(self.style.WARNING(f'\nTest Account Webhook Workflow'))
        self.stdout.write(f'  Webhook URL:  {webhook_url}')
        self.stdout.write(f'  Symbol:       {symbol}')
        self.stdout.write(f'  Volume:       {volume}')
        self.stdout.write(f'  Delay:        {delay}s')
        self.stdout.write(f'  Broker Type:  {broker_type}')
        self.stdout.write('')

        # Define the alert sequence
        if custom_id:
            buy_custom_id = 'b' + custom_id
            sell_custom_id = 's' + custom_id
        else:
            buy_custom_id = 'b15.Is1.1764170120313.1'
            sell_custom_id = 's15.Is1.1764170120313.1'

        alerts = []
        for action in actions:
            if action.startswith('xbuy'):
                pct = action.split(':')[1]
                alerts.append({'label': f'Partial Close {pct}%', 'message': f'X=BUY A={symbol} P={pct} ID={buy_custom_id} {extra_commands}'})
            elif action.startswith('xsell'):
                pct = action.split(':')[1]
                alerts.append({'label': f'Partial Close {pct}%', 'message': f'X=SELL A={symbol} P={pct} ID={sell_custom_id} {extra_commands}'})
            elif action == 'buy':
                alerts.append({'label': 'Buy Entry', 'message': f'D=BUY A={symbol} V={volume} ID={buy_custom_id} {extra_commands}'})
            elif action == 'sell':
                alerts.append({'label': 'Sell Entry', 'message': f'D=SELL A={symbol} V={volume} ID={sell_custom_id} {extra_commands}'})
            else:
                self.stdout.write(self.style.ERROR(f'Unknown action "{action}" — skipping'))

        total = len(alerts)
        results = []

        for i, alert in enumerate(alerts, 1):
            self.stdout.write(self.style.HTTP_INFO(f'[{i}/{total}] {alert["label"]}'))
            self.stdout.write(f'  Alert: {alert["message"]}')

            try:
                response = requests.post(
                    webhook_url,
                    data=alert['message'],
                    headers={'Content-Type': 'text/plain'},
                    timeout=30,
                )
                status = response.status_code
                try:
                    body = response.json()
                except Exception:
                    body = response.text

                if status == 200:
                    self.stdout.write(self.style.SUCCESS(f'  Status: {status} OK'))
                else:
                    self.stdout.write(self.style.ERROR(f'  Status: {status} FAILED'))

                self.stdout.write(f'  Response: {body}')
                results.append({'alert': alert['label'], 'status': status, 'response': body})

            except requests.exceptions.ConnectionError:
                self.stdout.write(self.style.ERROR(f'  Connection failed — is the server running?'))
                results.append({'alert': alert['label'], 'status': 'CONNECTION_ERROR', 'response': None})
            except requests.exceptions.Timeout:
                self.stdout.write(self.style.ERROR(f'  Request timed out'))
                results.append({'alert': alert['label'], 'status': 'TIMEOUT', 'response': None})
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {e}'))
                results.append({'alert': alert['label'], 'status': 'ERROR', 'response': str(e)})

            # Wait before sending the next alert (skip delay after the last one)
            if i < total:
                self.stdout.write(f'  Waiting {delay}s ...\n')
                time.sleep(delay)
            else:
                self.stdout.write('')

        # Summary
        self.stdout.write(self.style.WARNING('Summary'))
        passed = sum(1 for r in results if r['status'] == 200)
        failed = total - passed
        for r in results:
            icon = self.style.SUCCESS('PASS') if r['status'] == 200 else self.style.ERROR('FAIL')
            self.stdout.write(f'  {icon}  {r["alert"]}')

        self.stdout.write(f'\n  {passed}/{total} passed, {failed} failed\n')

        if failed > 0:
            raise CommandError(f'{failed} alert(s) failed.')

    def _detect_broker_type(self, webhook_id):
        """Auto-detect broker type by looking up the webhook_id in both account tables."""
        from automate.models import CryptoBrokerAccount, ForexBrokerAccount

        if CryptoBrokerAccount.objects.filter(custom_id=webhook_id).exists():
            return 'crypto'
        elif ForexBrokerAccount.objects.filter(custom_id=webhook_id).exists():
            return 'forex'
        else:
            raise CommandError(
                f'No account found with webhook ID "{webhook_id}". '
                f'Use --broker-type to specify manually.'
            )
