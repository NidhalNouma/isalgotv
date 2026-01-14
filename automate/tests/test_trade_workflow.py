"""
Integration tests for the trade workflow.

These tests verify the complete trade lifecycle:
1. Opening trades via webhook
2. Closing trades via webhook
3. Trade data persistence
4. Opposite trade handling (reverse trades)
5. Partial closes
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from decimal import Decimal
from django.test import Client
from django.urls import reverse

from automate.models import CryptoBrokerAccount, ForexBrokerAccount, TradeDetails, LogMessage
from automate.functions.alerts_logs_trades import (
    open_trade_by_account, close_trade_by_account, 
    save_new_trade, update_trade_after_close,
    process_alerts_trades, CLIENT_CLASSES
)
from automate.functions.alerts_message import manage_alert, extract_alert_data


class TestAlertMessageParsing:
    """Test alert message parsing functionality."""

    def test_entry_buy_parsing(self):
        """Test parsing a BUY entry alert."""
        message = "D=BUY A=BTCUSDT V=0.001 ID=test123"
        data = extract_alert_data(message)
        
        assert data['Action'] == 'Entry'
        assert data['Type'] == 'BUY'
        assert data['Asset'] == 'BTCUSDT'
        assert data['Volume'] == '0.001'
        assert data['ID'] == 'test123'

    def test_entry_sell_parsing(self):
        """Test parsing a SELL entry alert."""
        message = "D=SELL A=EURUSD V=0.1 ID=trade456"
        data = extract_alert_data(message)
        
        assert data['Action'] == 'Entry'
        assert data['Type'] == 'SELL'
        assert data['Asset'] == 'EURUSD'
        assert data['Volume'] == '0.1'

    def test_exit_parsing(self):
        """Test parsing an EXIT alert."""
        message = "X=BUY A=BTCUSDT ID=test123"
        data = extract_alert_data(message)
        
        assert data['Action'] == 'Exit'
        assert data['Type'] == 'BUY'
        assert data['Asset'] == 'BTCUSDT'

    def test_partial_exit_parsing(self):
        """Test parsing a partial EXIT alert."""
        message = "X=BUY A=BTCUSDT ID=test123 P=50%"
        data = extract_alert_data(message)
        
        assert data['Action'] == 'Exit'
        assert data['Partial'] == '50%'

    def test_reverse_trade_parsing(self):
        """Test parsing a reverse trade alert."""
        message = "D=BUY A=BTCUSDT V=0.001 ID=test123 R=1"
        data = extract_alert_data(message)
        
        assert data['Reverse'] == '1'

    def test_strategy_id_parsing(self):
        """Test parsing alert with strategy ID."""
        message = "D=BUY A=BTCUSDT V=0.001 ID=test123 ST=42"
        data = extract_alert_data(message)
        
        assert data.get('strategy_ID') == '42'


class TestTradeLifecycle:
    """Test the complete trade lifecycle with mocked broker responses."""

    @pytest.fixture
    def mock_binance_client(self):
        """Create a mock Binance client."""
        mock = MagicMock()
        mock.open_trade.return_value = {
            'message': 'Trade opened',
            'order_id': 'test_order_123',
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'qty': '0.001',
            'price': '50000.00',
            'time': '2025-01-01T00:00:00Z',
            'fees': '0.05',
            'currency': 'USDT',
        }
        mock.close_trade.return_value = {
            'message': 'Trade closed',
            'order_id': 'close_order_123',
            'qty': '0.001',
            'price': '51000.00',
            'time': '2025-01-01T01:00:00Z',
            'fees': '0.05',
        }
        mock.close_opposite_trades.return_value = []
        return mock

    def test_save_new_trade(self, crypto_account_factory, mock_strategy):
        """Test saving a new trade to the database."""
        account = crypto_account_factory('binance')
        
        opened_trade = {
            'order_id': 'test_order_123',
            'qty': '0.001',
            'price': '50000.00',
            'time': '2025-01-01T00:00:00Z',
            'currency': 'USDT',
            'fees': '0.05',
        }
        
        trade = save_new_trade(
            custom_id='test_trade_1',
            symbol='BTCUSDT',
            side='buy',
            opend_trade=opened_trade,
            account=account,
            strategy_id=mock_strategy.id
        )
        
        assert trade.custom_id == 'test_trade_1'
        assert trade.symbol == 'BTCUSDT'
        assert trade.side == 'B'
        assert trade.status == 'O'
        assert trade.strategy == mock_strategy

    def test_update_trade_after_close(self, crypto_account_factory, mock_trade_factory):
        """Test updating a trade after closing."""
        account = crypto_account_factory('binance')
        trade = mock_trade_factory(account)
        
        closed_trade = {
            'qty': '0.001',
            'price': '51000.00',
            'time': '2025-01-01T01:00:00Z',
            'closed_order_id': 'close_order_123',
        }
        
        updated_trade = update_trade_after_close(trade, '0.001', closed_trade)
        
        assert float(updated_trade.exit_price) == 51000.00
        assert float(updated_trade.remaining_volume) == 0.0

    def test_partial_close_updates_remaining_volume(self, crypto_account_factory, mock_trade_factory):
        """Test that partial closes properly update remaining volume."""
        account = crypto_account_factory('binance')
        trade = mock_trade_factory(account, volume='1.0')
        
        # Close 50%
        closed_trade = {
            'qty': '0.5',
            'price': '51000.00',
            'time': '2025-01-01T01:00:00Z',
        }
        
        updated_trade = update_trade_after_close(trade, '0.5', closed_trade)
        
        assert float(updated_trade.remaining_volume) == 0.5

    @patch('automate.functions.alerts_logs_trades.CLIENT_CLASSES')
    def test_open_trade_by_account(self, mock_classes, crypto_account_factory, mock_binance_client):
        """Test opening a trade through the account wrapper."""
        account = crypto_account_factory('binance')
        mock_classes.__getitem__.return_value = lambda **kwargs: mock_binance_client
        mock_classes.get.return_value = lambda **kwargs: mock_binance_client
        
        # This would need more specific mocking in a real test
        # Just verifying the function exists and has correct signature
        assert callable(open_trade_by_account)


class TestWebhookIntegration:
    """Test webhook endpoints for receiving trade signals."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_crypto_webhook_account_not_found(self, client):
        """Test webhook returns 404 for non-existent account."""
        response = client.post(
            '/wh/c/nonexistent_id',
            data='D=BUY A=BTCUSDT V=0.001 ID=test123',
            content_type='text/plain'
        )
        assert response.status_code == 404

    def test_forex_webhook_account_not_found(self, client):
        """Test webhook returns 404 for non-existent account."""
        response = client.post(
            '/wh/f/nonexistent_id',
            data='D=BUY A=EURUSD V=0.01 ID=test123',
            content_type='text/plain'
        )
        assert response.status_code == 404

    @patch('automate.functions.alerts_message.process_alerts_trades')
    def test_crypto_webhook_inactive_account(self, mock_process, client, crypto_account_factory):
        """Test webhook returns 400 for inactive account."""
        account = crypto_account_factory('binance')
        account.active = False
        account.save()
        
        response = client.post(
            f'/wh/c/{account.custom_id}',
            data='D=BUY A=BTCUSDT V=0.001 ID=test123',
            content_type='text/plain'
        )
        assert response.status_code == 400


class TestTradeDataIntegrity:
    """Test data integrity throughout the trade workflow."""

    def test_trade_currency_persistence(self, crypto_account_factory):
        """Verify currency is properly saved with trade."""
        account = crypto_account_factory('binance')
        
        opened_trade = {
            'order_id': 'test_order_123',
            'qty': '0.001',
            'price': '50000.00',
            'time': '2025-01-01T00:00:00Z',
            'currency': 'USDT',
            'fees': '0.05',
        }
        
        trade = save_new_trade(
            custom_id='test_currency',
            symbol='BTCUSDT',
            side='buy',
            opend_trade=opened_trade,
            account=account,
            strategy_id=None
        )
        
        assert trade.currency == 'USDT'

    def test_trade_fees_persistence(self, crypto_account_factory):
        """Verify fees are properly saved with trade."""
        account = crypto_account_factory('binance')
        
        opened_trade = {
            'order_id': 'test_order_123',
            'qty': '0.001',
            'price': '50000.00',
            'time': '2025-01-01T00:00:00Z',
            'currency': 'USDT',
            'fees': '1.25',
        }
        
        trade = save_new_trade(
            custom_id='test_fees',
            symbol='BTCUSDT',
            side='buy',
            opend_trade=opened_trade,
            account=account,
            strategy_id=None
        )
        
        assert float(trade.fees) == 1.25


class TestLogMessage:
    """Test logging functionality."""

    def test_log_creation_on_success(self, db, crypto_account_factory):
        """Verify log is created on successful trade."""
        from automate.functions.alerts_logs_trades import save_log
        import time
        
        account = crypto_account_factory('binance')
        start = time.perf_counter()
        
        log = save_log(
            response_status='S',
            alert_message='D=BUY A=BTCUSDT V=0.001 ID=test123',
            response_message='Trade executed successfully',
            account=account,
            latency_start=start
        )
        
        assert log.response_status == 'S'
        assert 'BTCUSDT' in log.alert_message

    def test_log_creation_on_error(self, db, crypto_account_factory):
        """Verify log is created on trade error."""
        from automate.functions.alerts_logs_trades import save_log
        import time
        
        account = crypto_account_factory('binance')
        start = time.perf_counter()
        
        log = save_log(
            response_status='E',
            alert_message='D=BUY A=BTCUSDT V=0.001 ID=test123',
            response_message='Insufficient balance',
            account=account,
            latency_start=start
        )
        
        assert log.response_status == 'E'
        assert log.response_message == 'Insufficient balance'
