"""
Live integration tests for broker connections.

⚠️ WARNING: These tests connect to REAL broker APIs!
- Only run with test/sandbox accounts
- Uses minimal volumes to minimize financial risk
- Requires actual API credentials in environment variables

To run these tests:
    pytest automate/tests/test_live_integration.py -v --live

Set environment variables for each broker you want to test:
    - BINANCE_TEST_API_KEY / BINANCE_TEST_API_SECRET
    - BYBIT_TEST_API_KEY / BYBIT_TEST_API_SECRET
    - etc.
"""
import pytest
import os
import time
from decimal import Decimal
from unittest.mock import patch

from automate.functions.alerts_logs_trades import CLIENT_CLASSES
from automate.tests.conftest import (
    CRYPTO_TEST_SYMBOLS, FOREX_TEST_SYMBOLS,
    CRYPTO_TEST_VOLUMES, FOREX_TEST_VOLUMES
)


# Skip all tests in this file unless --live flag is passed
def pytest_configure(config):
    config.addinivalue_line("markers", "live: mark test as live integration test")


@pytest.fixture
def skip_without_live(request):
    """Skip test if --live flag not provided."""
    if not request.config.getoption("--live", default=False):
        pytest.skip("Live tests skipped. Use --live to run.")


# =============================================================================
# Credential Fixtures (from environment variables)
# =============================================================================

@pytest.fixture
def binance_credentials():
    """Get Binance test credentials from environment."""
    api_key = os.environ.get('BINANCE_TEST_API_KEY')
    api_secret = os.environ.get('BINANCE_TEST_API_SECRET')
    if not api_key or not api_secret:
        pytest.skip("BINANCE_TEST_API_KEY and BINANCE_TEST_API_SECRET not set")
    return {'api_key': api_key, 'api_secret': api_secret}


@pytest.fixture
def bybit_credentials():
    """Get Bybit test credentials from environment."""
    api_key = os.environ.get('BYBIT_TEST_API_KEY')
    api_secret = os.environ.get('BYBIT_TEST_API_SECRET')
    if not api_key or not api_secret:
        pytest.skip("BYBIT_TEST_API_KEY and BYBIT_TEST_API_SECRET not set")
    return {'api_key': api_key, 'api_secret': api_secret}


@pytest.fixture
def tradelocker_credentials():
    """Get TradeLocker test credentials from environment."""
    username = os.environ.get('TRADELOCKER_TEST_USERNAME')
    password = os.environ.get('TRADELOCKER_TEST_PASSWORD')
    server = os.environ.get('TRADELOCKER_TEST_SERVER')
    if not all([username, password, server]):
        pytest.skip("TradeLocker credentials not set")
    return {'username': username, 'password': password, 'server': server}


@pytest.fixture
def metatrader_credentials():
    """Get MetaTrader test credentials from environment."""
    username = os.environ.get('MT5_TEST_USERNAME')
    password = os.environ.get('MT5_TEST_PASSWORD')
    server = os.environ.get('MT5_TEST_SERVER')
    if not all([username, password, server]):
        pytest.skip("MetaTrader credentials not set")
    return {'username': username, 'password': password, 'server': server}


# =============================================================================
# Live Credential Tests
# =============================================================================

@pytest.mark.live
class TestLiveCredentialValidation:
    """Test credential validation against live broker APIs."""

    def test_binance_credentials(self, skip_without_live, binance_credentials):
        """Test Binance API credential validation."""
        from automate.functions.brokers.binance import BinanceClient
        
        result = BinanceClient.check_credentials(
            binance_credentials['api_key'],
            binance_credentials['api_secret'],
            account_type='S'
        )
        
        assert result.get('valid') is True or 'error' not in result
        print(f"Binance credential check: {result}")

    def test_bybit_credentials(self, skip_without_live, bybit_credentials):
        """Test Bybit API credential validation."""
        from automate.functions.brokers.bybit import BybitClient
        
        result = BybitClient.check_credentials(
            bybit_credentials['api_key'],
            bybit_credentials['api_secret']
        )
        
        assert result.get('valid') is True or 'error' not in result
        print(f"Bybit credential check: {result}")

    def test_tradelocker_credentials(self, skip_without_live, tradelocker_credentials):
        """Test TradeLocker credential validation."""
        from automate.functions.brokers.tradelocker import TradeLockerClient
        
        result = TradeLockerClient.check_credentials(
            tradelocker_credentials['username'],
            tradelocker_credentials['password'],
            tradelocker_credentials['server'],
            type='D'
        )
        
        assert result.get('valid') is True or 'error' not in result
        print(f"TradeLocker credential check: {result}")


# =============================================================================
# Live Trade Tests (USE WITH CAUTION!)
# =============================================================================

@pytest.mark.live
@pytest.mark.slow
class TestLiveTradeExecution:
    """
    Test actual trade execution against live/sandbox APIs.
    
    ⚠️ WARNING: These tests will execute REAL trades!
    Only run with testnet/sandbox accounts.
    """

    def test_binance_open_close_trade(self, skip_without_live, binance_credentials, 
                                       crypto_account_factory, db):
        """Test opening and closing a trade on Binance testnet."""
        from automate.functions.brokers.binance import BinanceClient
        
        # Create account with real credentials
        account = crypto_account_factory(
            'binance',
            api_key=binance_credentials['api_key'],
            api_secret=binance_credentials['api_secret'],
            account_type='S'
        )
        
        client = BinanceClient(account=account)
        symbol = CRYPTO_TEST_SYMBOLS['binance']
        volume = CRYPTO_TEST_VOLUMES['binance']
        
        # Open BUY trade
        print(f"\n📈 Opening BUY trade: {volume} {symbol}")
        open_result = client.open_trade(symbol, 'BUY', volume, 'test_trade_1')
        
        assert 'order_id' in open_result
        assert open_result.get('side') == 'BUY'
        print(f"✅ Trade opened: {open_result}")
        
        # Wait a moment
        time.sleep(2)
        
        # Close the trade (SELL)
        print(f"\n📉 Closing trade: SELL {volume} {symbol}")
        close_result = client.close_trade(symbol, 'SELL', volume)
        
        assert 'order_id' in close_result
        print(f"✅ Trade closed: {close_result}")

    def test_full_trade_workflow_via_webhook_format(self, skip_without_live, 
                                                      binance_credentials,
                                                      crypto_account_factory, db):
        """Test complete trade workflow using webhook-style alerts."""
        from automate.functions.alerts_message import manage_alert
        
        # Create account with real credentials
        account = crypto_account_factory(
            'binance',
            api_key=binance_credentials['api_key'],
            api_secret=binance_credentials['api_secret'],
            account_type='S'
        )
        
        symbol = CRYPTO_TEST_SYMBOLS['binance']
        volume = CRYPTO_TEST_VOLUMES['binance']
        
        # Step 1: Open trade via alert message
        entry_message = f"D=BUY A={symbol} V={volume} ID=live_test_001"
        print(f"\n📈 Sending entry alert: {entry_message}")
        
        result = manage_alert(entry_message, account)
        print(f"Entry result: {result}")
        
        assert result.get('status') == 'completed' or 'error' not in result
        
        # Wait for trade to settle
        time.sleep(3)
        
        # Step 2: Close trade via alert message
        exit_message = f"X=BUY A={symbol} ID=live_test_001"
        print(f"\n📉 Sending exit alert: {exit_message}")
        
        result = manage_alert(exit_message, account)
        print(f"Exit result: {result}")
        
        assert result.get('status') == 'completed' or 'error' not in result


# =============================================================================
# Balance & Market Data Tests
# =============================================================================

@pytest.mark.live
class TestLiveMarketData:
    """Test fetching market data from live APIs."""

    def test_binance_get_balance(self, skip_without_live, binance_credentials,
                                  crypto_account_factory, db):
        """Test fetching account balance from Binance."""
        from automate.functions.brokers.binance import BinanceClient
        
        account = crypto_account_factory(
            'binance',
            api_key=binance_credentials['api_key'],
            api_secret=binance_credentials['api_secret']
        )
        
        client = BinanceClient(account=account)
        balance = client.get_account_balance()
        
        assert isinstance(balance, dict)
        print(f"\nBinance balance: {balance}")

    def test_binance_get_price(self, skip_without_live, binance_credentials,
                                crypto_account_factory, db):
        """Test fetching current price from Binance."""
        from automate.functions.brokers.binance import BinanceClient
        
        account = crypto_account_factory(
            'binance',
            api_key=binance_credentials['api_key'],
            api_secret=binance_credentials['api_secret']
        )
        
        client = BinanceClient(account=account)
        symbol = CRYPTO_TEST_SYMBOLS['binance']
        price = client.get_current_price(symbol)
        
        assert price > 0
        print(f"\n{symbol} price: {price}")

    def test_binance_get_exchange_info(self, skip_without_live, binance_credentials,
                                        crypto_account_factory, db):
        """Test fetching exchange info from Binance."""
        from automate.functions.brokers.binance import BinanceClient
        
        account = crypto_account_factory(
            'binance',
            api_key=binance_credentials['api_key'],
            api_secret=binance_credentials['api_secret']
        )
        
        client = BinanceClient(account=account)
        symbol = CRYPTO_TEST_SYMBOLS['binance']
        info = client.get_exchange_info(symbol)
        
        assert 'symbol' in info
        assert 'base_decimals' in info
        assert 'quote_decimals' in info
        print(f"\n{symbol} exchange info: {info}")


# =============================================================================
# Pytest Plugin for --live flag
# =============================================================================

def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run live integration tests against real broker APIs"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--live"):
        skip_live = pytest.mark.skip(reason="need --live option to run")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)
