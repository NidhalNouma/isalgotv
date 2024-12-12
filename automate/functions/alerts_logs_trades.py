from django.contrib.contenttypes.models import ContentType
from ..models import *
from .binance import check_binance_credentials, open_binance_trade, close_binance_trade
from .binance_us import check_binance_us_credentials, open_binance_us_trade, close_binance_us_trade
from .bitget import check_bitget_credentials, open_bitget_trade, close_bitget_trade

from .trade_locker import check_tradelocker_credentials, open_tradelocker_trade, close_tradelocker_trade

def check_crypto_credentials(broker_type, api_key, api_secret, phrase, trade_type="S"):
    print("Checking crypto credentials for " + broker_type)
    if broker_type == 'binance':
        return check_binance_credentials(api_key, api_secret, trade_type)
    if broker_type == 'binanceus':
        return check_binance_us_credentials(api_key, api_secret)
    elif broker_type == 'bitget':
        return check_bitget_credentials(api_key, api_secret, phrase)
    else:
        raise Exception("Unsupported broker type.")

def check_forex_credentials(broker_type, username, password, server, type="D"):
    
    if broker_type == 'tradelocker':
        return check_tradelocker_credentials(username, password, server, type)
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
        elif broker_type == 'tradelocker':
            return open_tradelocker_trade(account, symbol, side, volume)
        else:
            raise Exception("Unsupported broker type.")
    except Exception as e:
        print('open trade error: ', str(e))
        raise e
    

def close_trade_by_account(account, trade_to_close, symbol, side, volume_close):
    try:
        broker_type = account.broker_type
        if broker_type == 'binance':
            return close_binance_trade(account, trade_to_close.trade_type, symbol, side, volume_close)
        elif broker_type == 'binanceus':
            return close_binance_us_trade(account, trade_to_close.trade_type, symbol, side, volume_close)
        elif broker_type == 'bitget':
            return close_bitget_trade(account, trade_to_close.trade_type, symbol, side, volume_close)
        elif broker_type == 'tradelocker':
            return close_tradelocker_trade(account, trade_to_close.order_id, volume_close)
        else:
            raise Exception("Unsupported broker type.")
    except Exception as e:
        print('close trade error: ', str(e))
        raise e

def manage_alert(alert_message, account):
    try:
        print("Webhook request for account #" + str(account.id) + ": " + alert_message)
        alert_data = extract_alert_data(alert_message)
        
        action = alert_data.get('Action')
        custom_id = alert_data.get('ID')

        symbol = alert_data.get('Asset')
        side = alert_data.get('Type')

        partial = alert_data.get('Partial')
        volume = alert_data.get('Volume')

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
            trade = save_new_trade(custom_id, trade.get('order_id'), trade.get('symbol'), side, trade.get('qty'), trade.get('price', 0), account)
            save_log("S", alert_message, 'Order placed successfully.', account, trade)

        elif action == 'Exit':
            trade_to_close = get_trade(custom_id, symbol, side, account)
            if not trade_to_close:
                raise Exception(f"No trade found to close with ID: {custom_id}")

            volume_close = volume_to_close(trade_to_close, partial)
            closed_trade = close_trade_by_account(account, trade_to_close, symbol, side, volume_close)

            trade = update_trade_after_close(trade_to_close, volume_close, closed_trade.get('price', 0))
            save_log("S", alert_message, 'Order was closed successfully.', account, trade)

    except Exception as e:   
        print('API Error: %s' % e)
        save_log("E", alert_message, str(e), account)
        return {"error": str(e)}

def extract_alert_data(alert_message):
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
            data['Asset'] = value
        elif key == 'V':
            data['Volume'] = value
        elif key == 'P':
            data['Partial'] = value
        elif key == 'ID':
            data['ID'] = value
    
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

def save_new_trade(custom_id, order_id, symbol, side, volume, price, account):
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
            trade_type=getattr(account, 'type', None),
            content_type=content_type,
            object_id=account.id
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
    ).first()

    return trade

def update_trade_after_close(trade, closed_volume, price):
    trade.exit_price = price
    trade.remaining_volume = float(trade.remaining_volume) - float(closed_volume)
    if float(trade.remaining_volume) <= 0:
        trade.status = 'C'
    else:
        trade.status = 'P'
    trade.save()

    return trade

def volume_to_close(trade, partial):
    if partial:
        volume_to_close = float(trade.volume) * float(partial) / 100
        if volume_to_close > float(trade.remaining_volume):
            volume_to_close = float(trade.remaining_volume)
        return volume_to_close
    else:
        return float(trade.volume)