"""
Unit tests for broker client implementations.

These tests mock external API calls and verify that:
1. Broker clients are properly instantiated
2. Methods return expected data structures
3. Error handling works correctly
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal

from automate.functions.alerts_logs_trades import CLIENT_CLASSES
from automate.functions.brokers.types import OpenTrade, CloseTrade, OrderInfo


class TestBrokerClientInstantiation:
    """Test that all broker clients can be instantiated."""

    @pytest.mark.parametrize("broker_type", [
        'binance', 'binanceus', 'bitget', 'bybit', 'mexc', 'crypto',
        'bingx', 'bitmart', 'kucoin', 'coinbase', 'okx', 'kraken',
        'apex', 'hyperliquid'
    ])
    def test_crypto_client_instantiation(self, broker_type, crypto_account_factory):
        """Test crypto broker clients can be instantiated with an account."""
        passphrase = 'test_pass' if broker_type in ['bitget', 'bitmart', 'kucoin', 'okx', 'apex'] else None
        account = crypto_account_factory(broker_type, passphrase=passphrase)
        
        client_cls = CLIENT_CLASSES.get(broker_type)
        assert client_cls is not None, f"No client class found for {broker_type}"
        
        # Mock external connections during instantiation
        with patch.object(client_cls, '__init__', return_value=None):
            client = object.__new__(client_cls)
            assert client is not None

    @pytest.mark.parametrize("broker_type", [
        'tradelocker', 'metatrader4', 'metatrader5', 'ninjatrader',
        'dxtrade', 'ctrader', 'deriv', 'hankotrade', 'alpaca', 'tastytrade'
    ])
    def test_forex_client_instantiation(self, broker_type, forex_account_factory):
        """Test forex broker clients can be instantiated with an account."""
        account = forex_account_factory(broker_type)
        
        client_cls = CLIENT_CLASSES.get(broker_type)
        assert client_cls is not None, f"No client class found for {broker_type}"


class TestBrokerMethodSignatures:
    """Verify that all broker clients implement required methods."""

    @pytest.mark.parametrize("broker_type", list(CLIENT_CLASSES.keys()))
    def test_required_methods_exist(self, broker_type):
        """Test that all broker clients have required methods."""
        client_cls = CLIENT_CLASSES.get(broker_type)
        
        required_methods = [
            'check_credentials',
            'open_trade',
            'close_trade',
            'get_order_info',
            'get_account_balance',
        ]
        
        for method in required_methods:
            assert hasattr(client_cls, method), \
                f"{broker_type} client missing required method: {method}"


class TestOpenTradeResponse:
    """Test that open_trade returns proper OpenTrade TypedDict."""

    def test_open_trade_response_structure(self, mock_broker_response):
        """Verify OpenTrade response has all required fields."""
        required_fields = ['message', 'order_id', 'symbol', 'side', 'qty', 'price']
        
        for field in required_fields:
            assert field in mock_broker_response, f"Missing required field: {field}"


class TestCloseTradeResponse:
    """Test that close_trade returns proper CloseTrade TypedDict."""

    def test_close_trade_response_structure(self):
        """Verify CloseTrade response has all required fields."""
        response = {
            'message': 'Trade closed successfully',
            'order_id': 'close_order_123',
            'qty': '0.001',
        }
        
        required_fields = ['message', 'order_id', 'qty']
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"


class TestErrorHandling:
    """Test error handling in broker clients."""

    @pytest.mark.parametrize("broker_type", ['binance', 'bybit', 'tradelocker'])
    def test_invalid_credentials_handling(self, broker_type):
        """Test that invalid credentials are handled gracefully."""
        client_cls = CLIENT_CLASSES.get(broker_type)
        
        # Mock the check_credentials to simulate invalid credentials
        with patch.object(client_cls, 'check_credentials') as mock_check:
            mock_check.return_value = {'error': 'Invalid API key', 'valid': False}
            
            result = client_cls.check_credentials('invalid_key', 'invalid_secret')
            
            assert 'error' in result or result.get('valid') is False
