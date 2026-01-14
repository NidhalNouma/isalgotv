"""
Pytest configuration and fixtures for automate tests.
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.contrib.contenttypes.models import ContentType

from automate.models import CryptoBrokerAccount, ForexBrokerAccount, TradeDetails
from profile_user.models import User_Profile
from strategies.models import Strategy


# =============================================================================
# Test Configuration
# =============================================================================

# Define test symbols for each broker type
CRYPTO_TEST_SYMBOLS = {
    'binance': 'BTCUSDT',
    'binanceus': 'BTCUSD',
    'bitget': 'BTCUSDT',
    'bybit': 'BTCUSDT',
    'mexc': 'BTCUSDT',
    'crypto': 'BTC_USDT',
    'bingx': 'BTC-USDT',
    'bitmart': 'BTC_USDT',
    'kucoin': 'BTC-USDT',
    'coinbase': 'BTC-USD',
    'okx': 'BTC-USDT',
    'kraken': 'XBTUSD',
    'apex': 'BTCUSDT',
    'hyperliquid': 'BTC',
}

FOREX_TEST_SYMBOLS = {
    'tradelocker': 'EURUSD',
    'metatrader4': 'EURUSD',
    'metatrader5': 'EURUSD',
    'ninjatrader': 'ES',
    'dxtrade': 'EURUSD',
    'ctrader': 'EURUSD',
    'deriv': 'frxEURUSD',
    'hankotrade': 'EURUSD',
    'alpaca': 'AAPL',
    'tastytrade': 'AAPL',
}

# Minimum test volume per broker (very small to minimize risk)
CRYPTO_TEST_VOLUMES = {
    'binance': '0.001',
    'binanceus': '0.001',
    'bitget': '0.001',
    'bybit': '0.001',
    'mexc': '0.001',
    'crypto': '0.001',
    'bingx': '0.001',
    'bitmart': '0.001',
    'kucoin': '0.001',
    'coinbase': '0.0001',
    'okx': '0.001',
    'kraken': '0.0001',
    'apex': '0.001',
    'hyperliquid': '0.001',
}

FOREX_TEST_VOLUMES = {
    'tradelocker': '0.01',
    'metatrader4': '0.01',
    'metatrader5': '0.01',
    'ninjatrader': '1',
    'dxtrade': '0.01',
    'ctrader': '0.01',
    'deriv': '0.01',
    'hankotrade': '0.01',
    'alpaca': '1',
    'tastytrade': '1',
}


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_user_profile(db):
    """Create a mock user profile for testing."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    profile, _ = User_Profile.objects.get_or_create(user=user)
    return profile


@pytest.fixture
def mock_strategy(db, mock_user_profile):
    """Create a mock strategy for testing."""
    strategy, _ = Strategy.objects.get_or_create(
        name='Test Strategy',
        defaults={
            'user_profile': mock_user_profile,
            'description': 'Test strategy for automated tests'
        }
    )
    return strategy


@pytest.fixture
def crypto_account_factory(db, mock_user_profile):
    """Factory to create crypto broker accounts for testing."""
    def _create(broker_type, api_key='test_key', api_secret='test_secret', 
                account_type='S', passphrase=None):
        return CryptoBrokerAccount.objects.create(
            broker_type=broker_type,
            type=account_type,
            name=f'Test {broker_type} Account',
            apiKey=api_key,
            secretKey=api_secret,
            pass_phrase=passphrase,
            active=True,
            subscription_id='test_sub_123',
            created_by=mock_user_profile,
        )
    return _create


@pytest.fixture
def forex_account_factory(db, mock_user_profile):
    """Factory to create forex broker accounts for testing."""
    def _create(broker_type, username='testuser', password='testpass',
                server='demo.server.com', account_type='D', account_api_id='12345'):
        return ForexBrokerAccount.objects.create(
            broker_type=broker_type,
            type=account_type,
            name=f'Test {broker_type} Account',
            username=username,
            password=password,
            server=server,
            account_api_id=account_api_id,
            active=True,
            subscription_id='test_sub_123',
            created_by=mock_user_profile,
        )
    return _create


@pytest.fixture
def mock_trade_factory(db, mock_user_profile, crypto_account_factory):
    """Factory to create mock trade details."""
    def _create(account, symbol='BTCUSDT', side='B', volume='0.001', 
                entry_price='50000', status='O'):
        content_type = ContentType.objects.get_for_model(account.__class__)
        return TradeDetails.objects.create(
            custom_id='test_trade_123',
            order_id='order_123456',
            symbol=symbol,
            side=side,
            volume=volume,
            remaining_volume=volume,
            entry_price=Decimal(entry_price),
            entry_time='2025-01-01T00:00:00Z',
            status=status,
            content_type=content_type,
            object_id=account.id,
        )
    return _create


@pytest.fixture
def mock_broker_response():
    """Mock successful broker response for open/close trade."""
    return {
        'message': 'Trade executed successfully',
        'order_id': 'mock_order_123',
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'qty': '0.001',
        'price': '50000.00',
        'time': '2025-01-01T00:00:00Z',
        'fees': '0.05',
        'currency': 'USDT',
    }
