from django.contrib.contenttypes.models import ContentType

from decimal import Decimal
from django.utils import timezone

from ..models import *

from .binance import check_binance_credentials, open_binance_trade, close_binance_trade
from .binance_us import check_binance_us_credentials, open_binance_us_trade, close_binance_us_trade, get_binanceus_order_details
from .bitget import check_bitget_credentials, open_bitget_trade, close_bitget_trade
from .bybit import check_bybit_credentials, open_bybit_trade, close_bybit_trade
from .mexc import check_mexc_credentials, open_mexc_trade, close_mexc_trade
from .crypto import check_crypto_credentials as check_cryptocom_credentials, open_crypto_trade, close_crypto_trade, get_crypto_order_details 

from .trade_locker import check_tradelocker_credentials, open_tradelocker_trade, close_tradelocker_trade, get_tradelocker_trade_data
from .metatrader import add_metatrader_account, open_metatrader_trade, close_metatrader_trade, get_metatrader_trade_data

def check_crypto_credentials(broker_type, api_key, api_secret, phrase, trade_type="S"):
    print("Checking crypto credentials for " + broker_type)
    if broker_type == 'binance':
        return check_binance_credentials(api_key, api_secret, trade_type)
    if broker_type == 'binanceus':
        return check_binance_us_credentials(api_key, api_secret)
    elif broker_type == 'bitget':
        return check_bitget_credentials(api_key, api_secret, phrase, trade_type)
    elif broker_type == 'bybit':
        return check_bybit_credentials(api_key, api_secret, trade_type)
    elif broker_type == 'mexc':
        return check_mexc_credentials(api_key, api_secret, trade_type)
    elif broker_type == 'crypto':
        return check_cryptocom_credentials(api_key, api_secret, trade_type)
    else:
        raise Exception("Unsupported broker type.")

def check_forex_credentials(broker_type, username, password, server, type="D"):
    
    if broker_type == 'tradelocker':
        return check_tradelocker_credentials(username, password, server, type)
    elif broker_type == 'metatrader4':
        return add_metatrader_account(username, username, password, server, "mt4")
    elif broker_type == 'metatrader5':
        return add_metatrader_account(username, username, password, server, "mt5")
    else:
        raise Exception("Unsupported broker type.")

    
def open_trade_by_account(account, symbol, side, volume, custom_id):
    try:
        broker_type = account.broker_type
        if broker_type == 'binance':
            return open_binance_trade(account, symbol, side, volume, custom_id)
        elif broker_type == 'binanceus':
            return open_binance_us_trade(account, symbol, side, volume, custom_id)
        elif broker_type == 'bitget':
            return open_bitget_trade(account, symbol, side, volume)
        elif broker_type == 'bybit':
            return open_bybit_trade(account, symbol, side, volume)
        elif broker_type == 'mexc':
            return open_mexc_trade(account, symbol, side, volume)
        elif broker_type == 'crypto':
            return open_crypto_trade(account, symbol, side, volume)
        elif broker_type == 'tradelocker':
            return open_tradelocker_trade(account, symbol, side, volume)
        elif broker_type == 'metatrader4' or broker_type == 'metatrader5':
            return open_metatrader_trade(account, side.lower(), symbol, volume)
        else:
            raise Exception("Unsupported broker type.")
    except Exception as e:
        print('open trade error: ', str(e))
        raise e
    

def close_trade_by_account(account, trade_to_close, symbol, side, volume_close):
    try:
        broker_type = account.broker_type
        if broker_type == 'binance':
            return close_binance_trade(account, symbol, side, volume_close)
        elif broker_type == 'binanceus':
            return close_binance_us_trade(account, symbol, side, volume_close)
        elif broker_type == 'bitget':
            return close_bitget_trade(account, symbol, side, volume_close)
        elif broker_type == 'bybit':
            return close_bybit_trade(account, symbol, side, volume_close)
        elif broker_type == 'mexc':
            return close_mexc_trade(account, symbol, side, volume_close)
        elif broker_type == 'crypto':
            return close_crypto_trade(account, symbol, side, volume_close)
        elif broker_type == 'tradelocker':
            return close_tradelocker_trade(account, trade_to_close, volume_close)
        elif broker_type == 'metatrader4' or broker_type == 'metatrader5':
            return close_metatrader_trade(account, trade_to_close, volume_close)
        else:
            raise Exception("Unsupported broker type.")
    except Exception as e:
        print('close trade error: ', str(e))
        raise e

def get_trade_data(account, trade):
    try:
        broker_type = account.broker_type
        if broker_type == 'binanceus':
            return get_binanceus_order_details(account, trade)
        elif broker_type == 'crypto':
            return get_crypto_order_details(account, trade)
        elif broker_type == 'tradelocker':
            return get_tradelocker_trade_data(account, trade)
        elif broker_type == 'metatrader4' or broker_type == 'metatrader5':
            return get_metatrader_trade_data(account, trade)
        else:
            raise Exception("Unsupported broker type.")
    except Exception as e:
        print('close trade error: ', str(e))
        raise e

def manage_alert(alert_message, account):
    try:
        print("Webhook request for account #" + str(account.id) + ": " + alert_message)
        
        extra_symbol = ""
        if account.broker_type == 'binance' and account.type == "C":
            extra_symbol = "_PERP"

        alert_data = extract_alert_data(alert_message, extra_symbol)
        
        action = alert_data.get('Action')
        custom_id = alert_data.get('ID')

        symbol = alert_data.get('Asset')
        side = alert_data.get('Type')

        partial = alert_data.get('Partial')
        volume = alert_data.get('Volume')

        strategy_id = alert_data.get('strategy_ID', None)

        if not custom_id:
            raise Exception("No ID found in alert message.")

        if not action:
            raise Exception("No action found in alert message.")

        if not symbol:
            raise Exception("No symbol found in alert message.")

        if not side:
            raise Exception("No side found in alert message.")

        if not volume and action == 'Entry':
            raise Exception("No volume found in alert message.")

        if action == 'Entry':
            trade = open_trade_by_account(account, symbol, side, volume, custom_id)
            if trade.get('error') is not None:
                raise Exception(trade.get('error'))
            saved_trade = save_new_trade(custom_id, side, trade, account, strategy_id)
            save_log("S", alert_message, f'Order with ID {trade.get('order_id')} was placed successfully.', account, saved_trade)

        elif action == 'Exit':
            trade_to_close = get_trade(custom_id, symbol, side, account)
            if not trade_to_close:
                raise Exception(f"No trade found to close with ID: {custom_id}")

            volume_close = volume_to_close(trade_to_close, partial)
            closed_trade = close_trade_by_account(account, trade_to_close, symbol, side, volume_close)

            if closed_trade.get('error') is not None:
                raise Exception(closed_trade.get('error'))
            
            closed_volume = closed_trade.get('qty', volume_close)

            trade = update_trade_after_close(trade_to_close, closed_volume, closed_trade.get('price', 0), closed_trade.get('closed_order_id', ''))
            save_log("S", alert_message, f'Order with ID {trade_to_close.order_id} was closed successfully.', account, trade)

    except Exception as e:   
        print('API Error: %s' % e)
        save_log("E", alert_message, str(e), account)
        return {"error": str(e)}

def extract_alert_data(alert_message, extra_symbol=""):
    data = {}
    parts = alert_message.split()
    
    # Extract other fields from the message
    for part in parts:
        key, value = part.split('=')
        
        if key == 'D':
            data['Action'] = 'Entry'
            data['Type'] = value
        elif key == 'X':
            data['Action'] = 'Exit'
            data['Type'] = value
        elif key == 'A':
            data['Asset'] = value + extra_symbol
        elif key == 'V':
            data['Volume'] = value
        elif key == 'P':
            data['Partial'] = value
        elif key == 'ID' or key == 'NUM':
            data['ID'] = value
        elif key == 'ST' or key == 'ST_ID':
            data['strategy_ID'] = value
    
    return data

def save_log(response_status, alert_message, response_message, account, trade = None):
    if type(account) == CryptoBrokerAccount:
        log = LogMessage.objects.create(
            response_status=response_status,
            alert_message=alert_message,
            response_message=response_message,
            trade=trade,
            
            content_type=ContentType.objects.get_for_model(CryptoBrokerAccount),
            object_id=account.id
        )
    elif type(account) == ForexBrokerAccount:
        log = LogMessage.objects.create(
            response_status=response_status,
            alert_message=alert_message,
            response_message=response_message,
            trade=trade,
            
            content_type=ContentType.objects.get_for_model(ForexBrokerAccount),
            object_id=account.id
        )
    else:
        raise Exception("Account model not supported.")


    return log

def save_new_trade(custom_id, side, opend_trade, account, strategy_id):
    order_id = opend_trade.get('order_id') 
    symbol = opend_trade.get('symbol')
    volume = opend_trade.get('qty')
    price = opend_trade.get('price', 0)
    time = opend_trade.get('time', timezone.now())
    currency = opend_trade.get('currency', '')
    fees = opend_trade.get('fees', 0)
    closed_order_id = opend_trade.get('closed_order_id', '')

    t_side = "B" if str.lower(side) == "buy" else "S"
    
    if isinstance(account, (CryptoBrokerAccount, ForexBrokerAccount)):
        content_type = ContentType.objects.get_for_model(account.__class__)
        
        trade = TradeDetails.objects.create(
            custom_id=custom_id,
            order_id=order_id,
            symbol=symbol,
            side=t_side,
            volume=volume,
            remaining_volume=volume,
            entry_price=price,
            entry_time=time,
            currency=currency,
            fees=fees,
            closed_order_id=closed_order_id,
            trade_type=getattr(account, 'type', None),
            content_type=content_type,
            object_id=account.id,
            strategy_id=strategy_id
        )

    else:
        raise ValueError(f"Unsupported account model: {type(account)}")
    
    return trade

def get_trade(custom_id, symbol, side, account):
    t_side = "B" if str.lower(side) == "buy" else "S"

    content_type = ContentType.objects.get_for_model(account.__class__)

    trade = TradeDetails.objects.filter(
        custom_id=custom_id,
        symbol=symbol,
        side=t_side,
        content_type=content_type,
        object_id=account.id
    ).last()

    return trade

def update_trade_after_close(trade, closed_volume, price, closed_order_id):
    trade.exit_price = float(price)
    trade.closed_order_id = closed_order_id
    trade.remaining_volume = float(trade.remaining_volume) - float(closed_volume)
    if float(trade.remaining_volume) <= 0:
        trade.status = 'C'
    else:
        trade.status = 'P'
    trade.save()

    return trade

def volume_to_close(trade, partial):
    if partial:
        volume_to_close = Decimal(trade.volume) * Decimal(partial) / Decimal(100)
        print("Volume to close:", volume_to_close, 'from', trade.remaining_volume)
        
        if volume_to_close > Decimal(trade.remaining_volume):
            volume_to_close = Decimal(trade.remaining_volume)
        
        if Decimal(trade.remaining_volume) <= 0:
            raise Exception("No volume left to close.")
        
        # Return as a fixed-point decimal string
        return format(volume_to_close, 'f')
    else:
        # Return the full volume as a fixed-point decimal string
        return format(Decimal(trade.volume), 'f')