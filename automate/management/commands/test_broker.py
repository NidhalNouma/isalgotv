"""
Django management command to run trade workflow tests.

This provides an interactive way to test brokers without pytest,
directly from the Django shell or command line.

Usage:
    python manage.py test_broker binance --action credentials
    python manage.py test_broker binance --action open_close --symbol BTCUSDT --volume 0.001
    python manage.py test_broker tradelocker --action credentials --type D
    python manage.py test_broker --all --action credentials
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import time
import json

from automate.functions.alerts_logs_trades import (
    CLIENT_CLASSES, check_crypto_credentials, check_forex_credentials,
    open_trade_by_account, close_trade_by_account
)
from automate.models import CryptoBrokerAccount, ForexBrokerAccount


# Default test configuration
BROKER_CONFIGS = {
    # Crypto brokers
    'binance': {'type': 'crypto', 'symbol': 'BTCUSDT', 'volume': '0.001', 'account_type': 'S'},
    'binanceus': {'type': 'crypto', 'symbol': 'BTCUSD', 'volume': '0.001', 'account_type': 'S'},
    'bitget': {'type': 'crypto', 'symbol': 'BTCUSDT', 'volume': '0.001', 'account_type': 'S', 'needs_passphrase': True},
    'bybit': {'type': 'crypto', 'symbol': 'BTCUSDT', 'volume': '0.001', 'account_type': 'S'},
    'mexc': {'type': 'crypto', 'symbol': 'BTCUSDT', 'volume': '0.001', 'account_type': 'S'},
    'crypto': {'type': 'crypto', 'symbol': 'BTC_USDT', 'volume': '0.001', 'account_type': 'S'},
    'bingx': {'type': 'crypto', 'symbol': 'BTC-USDT', 'volume': '0.001', 'account_type': 'S'},
    'bitmart': {'type': 'crypto', 'symbol': 'BTC_USDT', 'volume': '0.001', 'account_type': 'S', 'needs_passphrase': True},
    'kucoin': {'type': 'crypto', 'symbol': 'BTC-USDT', 'volume': '0.001', 'account_type': 'S', 'needs_passphrase': True},
    'coinbase': {'type': 'crypto', 'symbol': 'BTC-USD', 'volume': '0.0001', 'account_type': 'S'},
    'okx': {'type': 'crypto', 'symbol': 'BTC-USDT', 'volume': '0.001', 'account_type': 'S', 'needs_passphrase': True},
    'kraken': {'type': 'crypto', 'symbol': 'XBTUSD', 'volume': '0.0001', 'account_type': 'S'},
    'apex': {'type': 'crypto', 'symbol': 'BTCUSDT', 'volume': '0.001', 'account_type': 'S', 'needs_passphrase': True},
    'hyperliquid': {'type': 'crypto', 'symbol': 'BTC', 'volume': '0.001', 'account_type': 'S'},
    
    # Forex brokers
    'tradelocker': {'type': 'forex', 'symbol': 'EURUSD', 'volume': '0.01'},
    'metatrader4': {'type': 'forex', 'symbol': 'EURUSD', 'volume': '0.01'},
    'metatrader5': {'type': 'forex', 'symbol': 'EURUSD', 'volume': '0.01'},
    'ninjatrader': {'type': 'forex', 'symbol': 'ES', 'volume': '1'},
    'dxtrade': {'type': 'forex', 'symbol': 'EURUSD', 'volume': '0.01'},
    'ctrader': {'type': 'forex', 'symbol': 'EURUSD', 'volume': '0.01'},
    'deriv': {'type': 'forex', 'symbol': 'frxEURUSD', 'volume': '0.01'},
    'hankotrade': {'type': 'forex', 'symbol': 'EURUSD', 'volume': '0.01'},
    'alpaca': {'type': 'forex', 'symbol': 'AAPL', 'volume': '1'},
    'tastytrade': {'type': 'forex', 'symbol': 'AAPL', 'volume': '1'},
}


class Command(BaseCommand):
    help = 'Test broker trade workflows'

    def add_arguments(self, parser):
        parser.add_argument(
            'broker',
            nargs='?',
            help='Broker type to test (e.g., binance, tradelocker)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test all brokers'
        )
        parser.add_argument(
            '--action',
            choices=['credentials', 'balance', 'open_close', 'full_workflow'],
            default='credentials',
            help='Test action to perform'
        )
        parser.add_argument(
            '--symbol',
            help='Trading symbol (overrides default)'
        )
        parser.add_argument(
            '--volume',
            help='Trading volume (overrides default)'
        )
        parser.add_argument(
            '--type',
            default='D',
            help='Account type (D=Demo, L=Live for forex; S=Spot, U=USDM, C=COINM for crypto)'
        )
        parser.add_argument(
            '--account-id',
            type=int,
            help='Use existing account ID instead of prompting for credentials'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be tested without executing'
        )

    def handle(self, *args, **options):
        if options['all']:
            brokers = list(BROKER_CONFIGS.keys())
        elif options['broker']:
            brokers = [options['broker']]
        else:
            raise CommandError('Please specify a broker or use --all')

        action = options['action']
        dry_run = options['dry_run']

        self.stdout.write(self.style.NOTICE(f"\n{'='*60}"))
        self.stdout.write(self.style.NOTICE(f"Trade Workflow Test - Action: {action.upper()}"))
        self.stdout.write(self.style.NOTICE(f"{'='*60}\n"))

        results = {}
        for broker in brokers:
            if broker not in BROKER_CONFIGS:
                self.stdout.write(self.style.ERROR(f"Unknown broker: {broker}"))
                continue

            config = BROKER_CONFIGS[broker]
            
            # Override config with command line options
            if options['symbol']:
                config['symbol'] = options['symbol']
            if options['volume']:
                config['volume'] = options['volume']
            if options['type']:
                if config['type'] == 'crypto':
                    config['account_type'] = options['type']

            self.stdout.write(self.style.NOTICE(f"\n--- Testing {broker.upper()} ---"))
            
            if dry_run:
                self.stdout.write(f"  Config: {json.dumps(config, indent=2)}")
                results[broker] = 'DRY RUN'
                continue

            try:
                if action == 'credentials':
                    result = self.test_credentials(broker, config, options)
                elif action == 'balance':
                    result = self.test_balance(broker, config, options)
                elif action == 'open_close':
                    result = self.test_open_close(broker, config, options)
                elif action == 'full_workflow':
                    result = self.test_full_workflow(broker, config, options)
                
                results[broker] = result
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error: {str(e)}"))
                results[broker] = {'error': str(e)}

        # Summary
        self.stdout.write(self.style.NOTICE(f"\n{'='*60}"))
        self.stdout.write(self.style.NOTICE("SUMMARY"))
        self.stdout.write(self.style.NOTICE(f"{'='*60}"))
        
        for broker, result in results.items():
            if isinstance(result, dict) and result.get('error'):
                self.stdout.write(self.style.ERROR(f"  ❌ {broker}: {result['error']}"))
            elif isinstance(result, dict) and result.get('valid'):
                self.stdout.write(self.style.SUCCESS(f"  ✅ {broker}: PASSED"))
            else:
                self.stdout.write(f"  ⚪ {broker}: {result}")

    def get_credentials(self, broker, config, options):
        """Get credentials either from existing account or user input."""
        if options.get('account_id'):
            # Use existing account
            if config['type'] == 'crypto':
                account = CryptoBrokerAccount.objects.get(id=options['account_id'])
                return {
                    'api_key': account.apiKey,
                    'api_secret': account.secretKey,
                    'passphrase': account.pass_phrase,
                    'account_type': account.type,
                    'account': account,
                }
            else:
                account = ForexBrokerAccount.objects.get(id=options['account_id'])
                return {
                    'username': account.username,
                    'password': account.password,
                    'server': account.server,
                    'account_api_id': account.account_api_id,
                    'account_type': account.type,
                    'account': account,
                }
        else:
            # Prompt for credentials
            self.stdout.write("  Enter credentials (leave blank to skip):")
            
            if config['type'] == 'crypto':
                api_key = input("    API Key: ").strip()
                if not api_key:
                    return None
                api_secret = input("    API Secret: ").strip()
                passphrase = None
                if config.get('needs_passphrase'):
                    passphrase = input("    Passphrase: ").strip()
                return {
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'passphrase': passphrase,
                    'account_type': config.get('account_type', 'S'),
                }
            else:
                username = input("    Username: ").strip()
                if not username:
                    return None
                password = input("    Password: ").strip()
                server = input("    Server: ").strip()
                account_id = input("    Account ID (if needed): ").strip() or None
                return {
                    'username': username,
                    'password': password,
                    'server': server,
                    'account_api_id': account_id,
                    'account_type': options.get('type', 'D'),
                }

    def test_credentials(self, broker, config, options):
        """Test credential validation."""
        creds = self.get_credentials(broker, config, options)
        if not creds:
            return {'skipped': True}

        self.stdout.write("  Testing credentials...")
        
        if config['type'] == 'crypto':
            result = check_crypto_credentials(
                broker,
                creds['api_key'],
                creds['api_secret'],
                creds.get('passphrase'),
                creds.get('account_type', 'S')
            )
        else:
            result = check_forex_credentials(
                broker,
                creds.get('username'),
                creds.get('password'),
                creds.get('server'),
                creds.get('account_type', 'D'),
                creds.get('account_api_id')
            )

        if result.get('valid'):
            self.stdout.write(self.style.SUCCESS(f"  ✅ Credentials valid!"))
        elif result.get('error'):
            self.stdout.write(self.style.ERROR(f"  ❌ Error: {result['error']}"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠️ Result: {result}"))

        return result

    def test_balance(self, broker, config, options):
        """Test fetching account balance."""
        creds = self.get_credentials(broker, config, options)
        if not creds:
            return {'skipped': True}

        self.stdout.write("  Fetching balance...")
        
        client_cls = CLIENT_CLASSES.get(broker)
        if not client_cls:
            raise CommandError(f"No client class for {broker}")

        # Create a mock account or use existing
        if creds.get('account'):
            account = creds['account']
        else:
            # Create temporary account object without saving
            if config['type'] == 'crypto':
                account = CryptoBrokerAccount(
                    broker_type=broker,
                    apiKey=creds['api_key'],
                    secretKey=creds['api_secret'],
                    pass_phrase=creds.get('passphrase'),
                    type=creds.get('account_type', 'S'),
                )
            else:
                account = ForexBrokerAccount(
                    broker_type=broker,
                    username=creds.get('username'),
                    password=creds.get('password'),
                    server=creds.get('server'),
                    account_api_id=creds.get('account_api_id'),
                    type=creds.get('account_type', 'D'),
                )

        client = client_cls(account=account)
        balance = client.get_account_balance()
        
        self.stdout.write(self.style.SUCCESS(f"  ✅ Balance retrieved:"))
        for asset, amounts in list(balance.items())[:5]:  # Show first 5
            self.stdout.write(f"    {asset}: {amounts}")

        return {'valid': True, 'balance': balance}

    def test_open_close(self, broker, config, options):
        """Test opening and closing a trade."""
        creds = self.get_credentials(broker, config, options)
        if not creds:
            return {'skipped': True}

        symbol = config['symbol']
        volume = config['volume']
        
        self.stdout.write(self.style.WARNING(
            f"  ⚠️ This will execute REAL trades! Symbol: {symbol}, Volume: {volume}"
        ))
        confirm = input("  Continue? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            return {'cancelled': True}

        client_cls = CLIENT_CLASSES.get(broker)
        if not client_cls:
            raise CommandError(f"No client class for {broker}")

        if creds.get('account'):
            account = creds['account']
        else:
            raise CommandError("Please use --account-id for trade execution tests")

        client = client_cls(account=account)
        
        # Open trade
        self.stdout.write(f"  📈 Opening BUY trade...")
        start = time.perf_counter()
        open_result = client.open_trade(symbol, 'BUY', volume, 'test_trade')
        open_latency = time.perf_counter() - start
        
        self.stdout.write(self.style.SUCCESS(
            f"  ✅ Trade opened in {open_latency:.2f}s: {open_result.get('order_id')}"
        ))

        # Wait
        time.sleep(2)

        # Close trade
        self.stdout.write(f"  📉 Closing trade...")
        start = time.perf_counter()
        close_result = client.close_trade(symbol, 'SELL', volume)
        close_latency = time.perf_counter() - start
        
        self.stdout.write(self.style.SUCCESS(
            f"  ✅ Trade closed in {close_latency:.2f}s: {close_result.get('order_id')}"
        ))

        return {
            'valid': True,
            'open_result': open_result,
            'close_result': close_result,
            'open_latency': open_latency,
            'close_latency': close_latency,
        }

    def test_full_workflow(self, broker, config, options):
        """Test full webhook-style workflow."""
        from automate.functions.alerts_message import manage_alert
        
        creds = self.get_credentials(broker, config, options)
        if not creds:
            return {'skipped': True}

        if not creds.get('account'):
            raise CommandError("Please use --account-id for full workflow tests")

        account = creds['account']
        symbol = config['symbol']
        volume = config['volume']

        self.stdout.write(self.style.WARNING(
            f"  ⚠️ This will execute REAL trades! Symbol: {symbol}, Volume: {volume}"
        ))
        confirm = input("  Continue? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            return {'cancelled': True}

        # Entry
        entry_msg = f"D=BUY A={symbol} V={volume} ID=test_workflow_001"
        self.stdout.write(f"  📈 Sending: {entry_msg}")
        
        start = time.perf_counter()
        entry_result = manage_alert(entry_msg, account)
        entry_latency = time.perf_counter() - start
        
        self.stdout.write(self.style.SUCCESS(f"  ✅ Entry processed in {entry_latency:.2f}s"))

        time.sleep(3)

        # Exit
        exit_msg = f"X=BUY A={symbol} ID=test_workflow_001"
        self.stdout.write(f"  📉 Sending: {exit_msg}")
        
        start = time.perf_counter()
        exit_result = manage_alert(exit_msg, account)
        exit_latency = time.perf_counter() - start
        
        self.stdout.write(self.style.SUCCESS(f"  ✅ Exit processed in {exit_latency:.2f}s"))

        return {
            'valid': True,
            'entry_result': entry_result,
            'exit_result': exit_result,
            'entry_latency': entry_latency,
            'exit_latency': exit_latency,
        }
