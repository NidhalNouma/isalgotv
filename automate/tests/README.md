# Automate App - Trade Workflow Testing Guide

## Overview

This testing framework provides multiple levels of testing for the trade automation workflow across all broker types.

## Test Structure

```
automate/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and configuration
│   ├── test_broker_clients.py   # Unit tests for broker clients
│   ├── test_trade_workflow.py   # Integration tests for trade lifecycle
│   └── test_live_integration.py # Live API tests (use with caution!)
├── management/
│   └── commands/
│       └── test_broker.py       # Django management command for interactive testing
```

## Quick Start

### 1. Run Unit Tests (No API calls)

```bash
# Run all unit tests
pytest automate/tests/ -v --ignore=automate/tests/test_live_integration.py

# Run specific test file
pytest automate/tests/test_trade_workflow.py -v

# Run with coverage
pytest automate/tests/ -v --cov=automate --cov-report=html
```

### 2. Interactive Testing via Management Command

```bash
# Test credentials for a specific broker
python manage.py test_broker binance --action credentials

# Test with an existing account
python manage.py test_broker binance --action balance --account-id 123

# Test all brokers (credential validation only)
python manage.py test_broker --all --action credentials

# Dry run to see what would be tested
python manage.py test_broker bybit --action open_close --dry-run

# Full workflow test (EXECUTES REAL TRADES)
python manage.py test_broker binance --action full_workflow --account-id 123
```

### 3. Live Integration Tests (⚠️ USE WITH CAUTION)

These tests connect to real broker APIs and can execute actual trades.

```bash
# Set environment variables first
export BINANCE_TEST_API_KEY="your_testnet_key"
export BINANCE_TEST_API_SECRET="your_testnet_secret"

# Run live tests
pytest automate/tests/test_live_integration.py -v --live
```

## Test Levels

### Level 1: Unit Tests (Mocked)
- **No API calls** - All external calls are mocked
- Tests broker client instantiation
- Tests method signatures
- Tests data structure validation
- Safe to run anytime

### Level 2: Integration Tests (Mocked)
- **No API calls** - Broker responses are mocked
- Tests complete trade lifecycle
- Tests webhook parsing
- Tests database operations
- Tests error handling

### Level 3: Live Credential Tests
- **API calls to check credentials only**
- No trades executed
- Verifies API keys work
- Tests account balance fetching

### Level 4: Live Trade Tests
- **⚠️ EXECUTES REAL TRADES**
- Use only with testnet/sandbox accounts
- Use minimal volumes
- Opens and closes small test trades

## Broker-Specific Test Configuration

### Crypto Brokers

| Broker | Test Symbol | Min Volume | Needs Passphrase |
|--------|-------------|------------|------------------|
| binance | BTCUSDT | 0.001 | No |
| binanceus | BTCUSD | 0.001 | No |
| bitget | BTCUSDT | 0.001 | Yes |
| bybit | BTCUSDT | 0.001 | No |
| mexc | BTCUSDT | 0.001 | No |
| crypto | BTC_USDT | 0.001 | No |
| bingx | BTC-USDT | 0.001 | No |
| bitmart | BTC_USDT | 0.001 | Yes |
| kucoin | BTC-USDT | 0.001 | Yes |
| coinbase | BTC-USD | 0.0001 | No |
| okx | BTC-USDT | 0.001 | Yes |
| kraken | XBTUSD | 0.0001 | No |
| apex | BTCUSDT | 0.001 | Yes |
| hyperliquid | BTC | 0.001 | No |

### Forex Brokers

| Broker | Test Symbol | Min Volume | Notes |
|--------|-------------|------------|-------|
| tradelocker | EURUSD | 0.01 | Demo/Live |
| metatrader4 | EURUSD | 0.01 | Demo/Live |
| metatrader5 | EURUSD | 0.01 | Demo/Live |
| ninjatrader | ES | 1 | Futures |
| dxtrade | EURUSD | 0.01 | Demo/Live |
| ctrader | EURUSD | 0.01 | Demo only (current) |
| deriv | frxEURUSD | 0.01 | Demo/Live |
| hankotrade | EURUSD | 0.01 | Demo/Live |
| alpaca | AAPL | 1 | Stocks |
| tastytrade | AAPL | 1 | Stocks/Options |

## Environment Variables

For live tests, set these environment variables:

```bash
# Binance (use testnet keys)
BINANCE_TEST_API_KEY=xxx
BINANCE_TEST_API_SECRET=xxx

# Bybit (use testnet keys)
BYBIT_TEST_API_KEY=xxx
BYBIT_TEST_API_SECRET=xxx

# TradeLocker
TRADELOCKER_TEST_USERNAME=xxx
TRADELOCKER_TEST_PASSWORD=xxx
TRADELOCKER_TEST_SERVER=xxx

# MetaTrader 5
MT5_TEST_USERNAME=xxx
MT5_TEST_PASSWORD=xxx
MT5_TEST_SERVER=xxx
```

## Testing Workflow Scenarios

### Scenario 1: Basic Entry/Exit

```
Entry: D=BUY A=BTCUSDT V=0.001 ID=test001
Exit:  X=BUY A=BTCUSDT ID=test001
```

### Scenario 2: Partial Exit

```
Entry:  D=BUY A=BTCUSDT V=0.01 ID=test002
Exit 1: X=BUY A=BTCUSDT ID=test002 P=50%
Exit 2: X=BUY A=BTCUSDT ID=test002
```

### Scenario 3: Reverse Trade

```
Entry 1: D=BUY A=BTCUSDT V=0.01 ID=test003
Entry 2: D=SELL A=BTCUSDT V=0.01 ID=test003 R=1
```

### Scenario 4: Strategy-Linked Trade

```
Entry: D=BUY A=BTCUSDT V=0.001 ID=test004 ST=42
Exit:  X=BUY A=BTCUSDT ID=test004 ST=42
```

## Adding Tests for New Brokers

1. Add broker config to `conftest.py`:
```python
CRYPTO_TEST_SYMBOLS['new_broker'] = 'BTCUSDT'
CRYPTO_TEST_VOLUMES['new_broker'] = '0.001'
```

2. Add to management command config:
```python
BROKER_CONFIGS['new_broker'] = {
    'type': 'crypto',
    'symbol': 'BTCUSDT',
    'volume': '0.001',
    'account_type': 'S'
}
```

3. Add parametrized tests if broker has unique behavior.

## Debugging Failed Tests

### Check Logs
```python
from automate.models import LogMessage

# Get recent logs for an account
logs = LogMessage.objects.filter(object_id=account.id).order_by('-created_at')[:10]
for log in logs:
    print(f"{log.response_status}: {log.response_message}")
```

### Check Trade Status
```python
from automate.models import TradeDetails

# Get trades for an account
trades = TradeDetails.objects.filter(object_id=account.id).order_by('-entry_time')[:10]
for trade in trades:
    print(f"{trade.symbol} {trade.side} {trade.status} - {trade.remaining_volume}")
```

## CI/CD Integration

For CI pipelines, run only mocked tests:

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    pytest automate/tests/ -v \
      --ignore=automate/tests/test_live_integration.py \
      --cov=automate \
      --cov-report=xml
```

## Best Practices

1. **Never run live tests in production** - Use testnet/sandbox accounts only
2. **Use minimal volumes** - The configured volumes are intentionally small
3. **Check account balance first** - Ensure test account has sufficient funds
4. **Monitor logs** - Check LogMessage for any errors
5. **Clean up test trades** - Delete test trades after testing
6. **Use unique IDs** - Prevent conflicts with real trades

## Troubleshooting

### "Account not found" errors
- Verify the account exists and `custom_id` matches
- Check `account.active` is True

### "Insufficient balance" errors
- Fund the test account
- Reduce volume parameter

### Timeout errors
- Check broker API status
- Increase timeout in broker client

### "Invalid credentials" errors
- Verify API keys are correct
- Check if IP whitelist is configured
- Ensure API permissions are sufficient
