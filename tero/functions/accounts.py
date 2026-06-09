from automate.functions.alerts_logs_trades import CLIENT_CLASSES
from automate.models import *
from django.utils.translation import gettext as _


def _serialize_trade(trade: TradeDetails):
    """Convert a TradeDetails instance into a tool-friendly dictionary."""
    return {
        "id": trade.id,
        "custom_id": trade.custom_id,
        "order_id": trade.order_id,
        "closed_order_id": trade.closed_order_id,
        "symbol": trade.symbol,
        "side": trade.side,
        "status": trade.status,
        "volume": str(trade.volume),
        "remaining_volume": str(trade.remaining_volume),
        "entry_price": str(trade.entry_price),
        "exit_price": str(trade.exit_price),
        "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
        "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
        "fees": str(trade.fees),
        "profit": str(trade.profit),
        "net_profit": str(trade.net_profit),
        "currency": trade.currency,
        "trade_type": trade.trade_type,
        "fills": trade.fills,
        "additional_info": trade.additional_info,
        "account_id": trade.object_id,
    }

def get_automate_account(account_id, broker):
    """
    Retrieve an automate account by its ID and broker type.
    """
    try:
        broker_value = (str(broker).strip() if broker is not None else "")
        broker_lower = broker_value.lower()
        broker_upper = broker_value.upper()

        crypto_brokers = {value for value, _label in CryptoBrokerAccount.BROKER_TYPES}
        forex_brokers = {value for value, _label in ForexBrokerAccount.BROKER_TYPES}

        # Support account category values from older context payloads.
        if broker_upper == "CRYPTO":
            return CryptoBrokerAccount.objects.get(id=account_id)
        if broker_upper == "FOREX":
            return ForexBrokerAccount.objects.get(id=account_id)

        # Support concrete broker values from UI context (e.g. "apex", "binance").
        if broker_lower in crypto_brokers:
            return CryptoBrokerAccount.objects.get(id=account_id, broker_type=broker_lower)
        if broker_lower in forex_brokers:
            return ForexBrokerAccount.objects.get(id=account_id, broker_type=broker_lower)

        # Final fallback: resolve by id across both tables.
        try:
            return CryptoBrokerAccount.objects.get(id=account_id)
        except CryptoBrokerAccount.DoesNotExist:
            return ForexBrokerAccount.objects.get(id=account_id)
    except (CryptoBrokerAccount.DoesNotExist, ForexBrokerAccount.DoesNotExist):
        return None


def get_automate_account_class(account):
    try:
        broker_type = account.broker_type
        
        client_cls = CLIENT_CLASSES.get(broker_type)
        if client_cls is None:
            raise Exception(_("Unsupported broker type: %s") % broker_type)
        
        return client_cls
    except Exception as e:
        raise Exception(_("Error retrieving client class for broker type '%s': %s") % (broker_type, str(e)))


def get_saved_trade_info(trade_id):
    """
    Retrieve trade information for a given account and trade ID.
    """
    try:
        trade = TradeDetails.objects.get(id=trade_id)
        return _serialize_trade(trade)
    
    except Exception as e:
        raise Exception(_("Error retrieving saved trade info for trade ID '%s': %s") % (trade_id, str(e)))

def get_saved_open_trades(account):
    """
    Retrieve a list of currently open trades for a given account.
    """
    try:
        content_type = ContentType.objects.get_for_model(account.__class__)
        open_trades = TradeDetails.objects.filter(status__in=['O', 'P'], content_type=content_type, object_id=account.id)
        return [_serialize_trade(trade) for trade in open_trades]
    except Exception as e:
        raise Exception(_("Error retrieving open trades for account '%s': %s") % (account.id, str(e)))

def get_account_balance(account):
    try:
        # print(f"Getting balance for account {account.id} ({account.broker_type})")
        cls = get_automate_account_class(account)
        client = cls(account=account)
        balance = client.get_account_balance()
        return balance
    except Exception as e:
        # print(f"Error getting balance for account {account.id}: {str(e)}")
        raise Exception(_("Error retrieving balance for account '%s': %s") % (account.id, str(e)))


def get_symbol_info(account, symbol: str):
    """
    Retrieve exchange information for a given symbol.
    Returns symbol details like min/max order size, precision, etc.
    """
    try:
        cls = get_automate_account_class(account)
        client = cls(account=account)
        info = client.get_exchange_info(symbol)
        return info
    except Exception as e:
        raise Exception(_("Error retrieving symbol info for '%s': %s") % (symbol, str(e)))


def get_current_price(account, symbol: str):
    """
    Retrieve the current market price for a given symbol.
    """
    try:
        cls = get_automate_account_class(account)
        client = cls(account=account)
        price = client.get_current_price(symbol)
        return price
    except Exception as e:
        raise Exception(_("Error retrieving current price for '%s': %s") % (symbol, str(e)))


def get_available_trading_pairs(account):
    """
    Retrieve the list of all available trading pairs on the broker.
    """
    try:
        cls = get_automate_account_class(account)
        client = cls(account=account)
        pairs = client.get_trading_pairs()
        return pairs
    except Exception as e:
        raise Exception(_("Error retrieving available trading pairs for account '%s': %s") % (account.id, str(e)))


def get_order_book_data(account, symbol: str, limit: int = 20):
    """
    Retrieve the order book (bid/ask data) for a given symbol.
    
    Args:
        account: The broker account
        symbol: The trading pair symbol (e.g., 'BTC/USDT')
        limit: Maximum number of bids/asks to return (default: 20)
    """
    try:
        cls = get_automate_account_class(account)
        client = cls(account=account)
        order_book = client.get_order_book(symbol, limit)
        return order_book
    except Exception as e:
        raise Exception(_("Error retrieving order book for '%s': %s") % (symbol, str(e)))


def get_market_candles(account, symbol: str, interval: str, limit: int = 100):
    """
    Retrieve historical candlestick data for technical analysis.
    
    Args:
        account: The broker account
        symbol: The trading pair symbol (e.g., 'BTC/USDT')
        interval: Timeframe (e.g., '1m', '5m', '1h', '4h', '1d')
        limit: Number of candles to return (default: 100, max: 500)
    """
    try:
        cls = get_automate_account_class(account)
        client = cls(account=account)
        candles = client.get_history_candles(symbol, interval, limit)
        return candles
    except Exception as e:
        raise Exception(_("Error retrieving candles for '%s' on '%s': %s") % (symbol, interval, str(e)))


def open_trade_for_account(account, symbol: str, side: str, quantity: float, custom_id: str = None):
    """
    Open a trade on the broker.

    Args:
        account: The broker account
        symbol: The trading pair symbol (e.g., 'BTC/USDT')
        side: 'BUY' or 'SELL'
        quantity: The amount to trade
        custom_id: Optional custom order identifier
    """
    try:
        cls = get_automate_account_class(account)
        client = cls(account=account)
        result = client.open_trade(symbol, side, quantity, custom_id)
        return result
    except Exception as e:
        raise Exception(_("Error opening trade for '%s': %s") % (symbol, str(e)))


def close_trade_for_account(account, symbol: str, side: str, quantity: float):
    """
    Close an open trade position on the broker.

    Args:
        account: The broker account
        symbol: The trading pair symbol (e.g., 'BTC/USDT')
        side: The closing side — 'BUY' to close a short, 'SELL' to close a long
        quantity: The amount to close
    """
    try:
        cls = get_automate_account_class(account)
        client = cls(account=account)
        result = client.close_trade(symbol, side, quantity)
        return result
    except Exception as e:
        raise Exception(_("Error closing trade for '%s': %s") % (symbol, str(e)))


def get_order_info_for_account(account, symbol: str, order_id: str):
    """
    Retrieve information for a specific order by its ID.

    Args:
        account: The broker account
        symbol: The trading pair symbol
        order_id: The broker order ID to look up
    """
    try:
        cls = get_automate_account_class(account)
        client = cls(account=account)
        result = client.get_order_info(symbol, order_id)
        return result
    except Exception as e:
        raise Exception(_("Error retrieving order info for '%s' order '%s': %s") % (symbol, order_id, str(e)))