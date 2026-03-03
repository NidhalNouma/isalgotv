"""
Tests for the `automate` management command.

The command sends a configurable sequence of webhook alerts to test the
full automation pipeline (entry, partial close, full close) for both
buy and sell directions.

Usage of the command being tested:
    python manage.py automate <webhook_id> --volume 0.001 --symbol BTCUSDT
"""
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock, call

from django.core.management import call_command
from django.core.management.base import CommandError

from automate.tests.conftest import (
    DEFAULT_AUTOMATE_ACTIONS,
    DEFAULT_BUY_CUSTOM_ID,
    DEFAULT_SELL_CUSTOM_ID,
)


# =============================================================================
# Helpers
# =============================================================================

def _mock_response(status_code=200, body=None):
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body or {'status': 'ok'}
    resp.text = str(body or {'status': 'ok'})
    return resp


def _run_command(*args, **kwargs):
    """Call the automate management command, return (stdout, stderr)."""
    out = StringIO()
    err = StringIO()
    call_command('automate', *args, stdout=out, stderr=err, **kwargs)
    return out.getvalue(), err.getvalue()


# =============================================================================
# Action Parsing & Alert Building
# =============================================================================

class TestActionParsing:
    """Verify the command correctly translates --actions into alert messages."""

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_default_actions_produces_six_alerts(self, mock_post, db):
        """Default --actions should produce 6 alerts (buy, xbuy:60, xbuy:100,
        sell, xsell:60, xsell:100)."""
        _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
        )
        assert mock_post.call_count == 6

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_custom_actions_subset(self, mock_post, db):
        """Only the specified actions should fire."""
        _run_command(
            'wh123', '--volume', '0.01', '--symbol', 'EURUSD',
            '--delay', '0', '--broker-type', 'forex',
            '--base-url', 'http://localhost',
            '--actions', 'buy,xbuy:100',
        )
        assert mock_post.call_count == 2

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_sell_only_actions(self, mock_post, db):
        """Sell-only actions should work."""
        _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--actions', 'sell,xsell:100',
        )
        assert mock_post.call_count == 2


# =============================================================================
# Alert Message Content
# =============================================================================

class TestAlertMessageContent:
    """Ensure the POST body sent to the webhook has the correct format."""

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_buy_entry_message_format(self, mock_post, db):
        """A 'buy' action should produce D=BUY A=<symbol> V=<volume> ID=<buy_id>."""
        _run_command(
            'wh123', '--volume', '0.05', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--actions', 'buy',
        )
        body = mock_post.call_args.kwargs.get('data') or mock_post.call_args[1].get('data')
        assert 'D=BUY' in body
        assert 'A=BTCUSDT' in body
        assert 'V=0.05' in body
        assert f'ID={DEFAULT_BUY_CUSTOM_ID}' in body

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_sell_entry_message_format(self, mock_post, db):
        """A 'sell' action should produce D=SELL A=<symbol> V=<volume> ID=<sell_id>."""
        _run_command(
            'wh123', '--volume', '0.01', '--symbol', 'EURUSD',
            '--delay', '0', '--broker-type', 'forex',
            '--base-url', 'http://localhost',
            '--actions', 'sell',
        )
        body = mock_post.call_args.kwargs.get('data') or mock_post.call_args[1].get('data')
        assert 'D=SELL' in body
        assert 'A=EURUSD' in body
        assert f'ID={DEFAULT_SELL_CUSTOM_ID}' in body

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_partial_close_message_format(self, mock_post, db):
        """xbuy:60 should produce X=BUY … P=60."""
        _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--actions', 'xbuy:60',
        )
        body = mock_post.call_args.kwargs.get('data') or mock_post.call_args[1].get('data')
        assert 'X=BUY' in body
        assert 'P=60' in body

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_full_close_message_format(self, mock_post, db):
        """xsell:100 should produce X=SELL … P=100."""
        _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--actions', 'xsell:100',
        )
        body = mock_post.call_args.kwargs.get('data') or mock_post.call_args[1].get('data')
        assert 'X=SELL' in body
        assert 'P=100' in body

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_extra_commands_appended(self, mock_post, db):
        """--extra-commands should appear in every alert body."""
        _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--actions', 'buy',
            '--extra-commands', 'T=1 SL=49000 TP=55000',
        )
        body = mock_post.call_args.kwargs.get('data') or mock_post.call_args[1].get('data')
        assert 'T=1' in body
        assert 'SL=49000' in body
        assert 'TP=55000' in body


# =============================================================================
# Custom IDs
# =============================================================================

class TestCustomIdHandling:
    """The command should use default IDs or honour --custom-id."""

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_default_custom_ids(self, mock_post, db):
        """Without --custom-id, the command uses built-in default IDs."""
        _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--actions', 'buy,sell',
        )
        # buy alert
        buy_body = mock_post.call_args_list[0].kwargs.get('data') or mock_post.call_args_list[0][1].get('data')
        assert f'ID={DEFAULT_BUY_CUSTOM_ID}' in buy_body
        # sell alert
        sell_body = mock_post.call_args_list[1].kwargs.get('data') or mock_post.call_args_list[1][1].get('data')
        assert f'ID={DEFAULT_SELL_CUSTOM_ID}' in sell_body

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_custom_id_override(self, mock_post, db):
        """--custom-id should prefix 'b'/'s' to the provided value."""
        _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--custom-id', 'myID.42',
            '--actions', 'buy,sell',
        )
        buy_body = mock_post.call_args_list[0].kwargs.get('data') or mock_post.call_args_list[0][1].get('data')
        assert 'ID=bmyID.42' in buy_body
        sell_body = mock_post.call_args_list[1].kwargs.get('data') or mock_post.call_args_list[1][1].get('data')
        assert 'ID=smyID.42' in sell_body


# =============================================================================
# Webhook URL Construction
# =============================================================================

class TestWebhookUrlConstruction:
    """Verify the correct URL is built from --broker-type and --base-url."""

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_crypto_url_path(self, mock_post, db):
        """Crypto accounts should POST to /c/<webhook_id>."""
        _run_command(
            'my_wh', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--actions', 'buy',
        )
        url = mock_post.call_args.kwargs.get('url') or mock_post.call_args[0][0]
        assert url == 'http://localhost/c/my_wh'

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_forex_url_path(self, mock_post, db):
        """Forex accounts should POST to /f/<webhook_id>."""
        _run_command(
            'fx_wh', '--volume', '0.01', '--symbol', 'EURUSD',
            '--delay', '0', '--broker-type', 'forex',
            '--base-url', 'http://localhost',
            '--actions', 'sell',
        )
        url = mock_post.call_args.kwargs.get('url') or mock_post.call_args[0][0]
        assert url == 'http://localhost/f/fx_wh'


# =============================================================================
# Broker Type Auto-Detection
# =============================================================================

class TestBrokerTypeAutoDetection:
    """When --broker-type is omitted, the command should auto-detect from DB."""

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    @patch('automate.models.CryptoBrokerAccount.objects')
    def test_auto_detect_crypto(self, mock_crypto_qs, mock_post):
        """Auto-detect crypto when webhook_id matches a CryptoBrokerAccount."""
        mock_crypto_qs.filter.return_value.exists.return_value = True
        _run_command(
            'crypto_wh', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--base-url', 'http://localhost',
            '--actions', 'buy',
        )
        url = mock_post.call_args.kwargs.get('url') or mock_post.call_args[0][0]
        assert '/c/' in url

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    @patch('automate.models.ForexBrokerAccount.objects')
    @patch('automate.models.CryptoBrokerAccount.objects')
    def test_auto_detect_forex(self, mock_crypto_qs, mock_forex_qs, mock_post):
        """Auto-detect forex when webhook_id matches a ForexBrokerAccount."""
        mock_crypto_qs.filter.return_value.exists.return_value = False
        mock_forex_qs.filter.return_value.exists.return_value = True
        _run_command(
            'forex_wh', '--volume', '0.01', '--symbol', 'EURUSD',
            '--delay', '0', '--base-url', 'http://localhost',
            '--actions', 'sell',
        )
        url = mock_post.call_args.kwargs.get('url') or mock_post.call_args[0][0]
        assert '/f/' in url

    @patch('automate.models.ForexBrokerAccount.objects')
    @patch('automate.models.CryptoBrokerAccount.objects')
    def test_auto_detect_raises_on_unknown_id(self, mock_crypto_qs, mock_forex_qs):
        """Unknown webhook_id should raise CommandError when no --broker-type."""
        mock_crypto_qs.filter.return_value.exists.return_value = False
        mock_forex_qs.filter.return_value.exists.return_value = False
        with pytest.raises(CommandError, match='No account found'):
            _run_command(
                'nonexistent_wh', '--volume', '0.001', '--symbol', 'BTCUSDT',
                '--delay', '0', '--base-url', 'http://localhost',
                '--actions', 'buy',
            )


# =============================================================================
# Error Handling & Summary
# =============================================================================

class TestErrorHandling:
    """Ensure the command handles failed requests and raises on failures."""

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response(status_code=400, body={'error': 'Bad request'}))
    def test_failed_alert_raises_command_error(self, mock_post, db):
        """CommandError should be raised when any alert returns non-200."""
        with pytest.raises(CommandError, match='failed'):
            _run_command(
                'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
                '--delay', '0', '--broker-type', 'crypto',
                '--base-url', 'http://localhost',
                '--actions', 'buy',
            )

    @patch('automate.management.commands.automate.requests.post',
           side_effect=Exception('Connection refused'))
    def test_connection_error_raises_command_error(self, mock_post, db):
        """Network errors should be caught and counted as failures."""
        with pytest.raises(CommandError, match='failed'):
            _run_command(
                'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
                '--delay', '0', '--broker-type', 'crypto',
                '--base-url', 'http://localhost',
                '--actions', 'buy',
            )

    @patch('automate.management.commands.automate.requests.post')
    def test_mixed_results_reports_correctly(self, mock_post, db):
        """When some alerts pass and some fail, summary should reflect both."""
        mock_post.side_effect = [
            _mock_response(200),   # buy  → PASS
            _mock_response(400),   # xbuy → FAIL
        ]
        with pytest.raises(CommandError, match='1 alert'):
            out, _ = _run_command(
                'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
                '--delay', '0', '--broker-type', 'crypto',
                '--base-url', 'http://localhost',
                '--actions', 'buy,xbuy:100',
            )

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_all_pass_no_error(self, mock_post, db):
        """When all alerts pass, no CommandError should be raised."""
        out, _ = _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
        )
        assert '6/6 passed' in out


# =============================================================================
# Output & Summary
# =============================================================================

class TestCommandOutput:
    """Verify the command prints expected diagnostic information."""

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_output_contains_webhook_url(self, mock_post, db):
        out, _ = _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://myhost',
            '--actions', 'buy',
        )
        assert 'http://myhost/c/wh123' in out

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_output_contains_symbol_and_volume(self, mock_post, db):
        out, _ = _run_command(
            'wh123', '--volume', '0.05', '--symbol', 'ETHUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--actions', 'buy',
        )
        assert 'ETHUSDT' in out
        assert '0.05' in out

    @patch('automate.management.commands.automate.requests.post',
           return_value=_mock_response())
    def test_output_contains_summary_section(self, mock_post, db):
        out, _ = _run_command(
            'wh123', '--volume', '0.001', '--symbol', 'BTCUSDT',
            '--delay', '0', '--broker-type', 'crypto',
            '--base-url', 'http://localhost',
            '--actions', 'buy',
        )
        assert 'Summary' in out
        assert '1/1 passed' in out
