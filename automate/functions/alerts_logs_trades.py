from ..models import *
from .binance import * 
from .binance_us import *
from .bitget import *

from .trade_locker import *

def check_crypto_credentials(broker_type, api_key, api_secret, phrase, trade_type="S"):
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

    

def manage_alert(alert_message, account):
    try:
        print("Webhook request for account #" + str(account.id) + ": " + alert_message)
        alert_data = extract_alert_data(alert_message)
        broker_type = account.broker_type
        
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

        if broker_type == 'binance':
            if action == 'Entry':
                trade = open_binance_trade(account, symbol, side, volume, custom_id)
                trade =save_new_trade(custom_id, trade.order_id, trade.symbol, side, trade.origQty, trade.price, account)
                save_log("S", alert_message, 'Order placed successfully.', account, trade)
                print(trade)

            elif action == 'Exit':
                trade_to_close = get_trade(custom_id, symbol, side, account)
                if not trade_to_close:
                    raise Exception(f"No trade found to close with ID: {custom_id}")
                volume_to_close = volume
                if partial:
                    volume_to_close = trade_to_close.volume * float(partial) / 100
                closed_trade = close_binance_trade(account, trade_to_close.trade_type, symbol, side, volume_to_close)

                trade = update_trade_after_close(trade_to_close, volume_to_close, closed_trade.price)
                save_log("S", alert_message, 'Order was closed successfully.', account, trade)
                print(closed_trade)
    
    except Exception as e:   
        print('webhook error: %s' % e)
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
    if trade is None:
        log = CryptoLogMessage.objects.create(
            response_status=response_status,
            alert_message=alert_message,
            response_message=response_message,
            account=account,
        )
    else:
        log = CryptoLogMessage.objects.create(
            response_status=response_status,
            alert_message=alert_message,
            response_message=response_message,
            trade=trade,
            account=account,
        )
    return log

def save_new_trade(custom_id, order_id, symbol, side, volume, price, account):
    t_side = "B" if str.lower(side) == "buy" else "S"

    trade = CryptoTradeDetails.objects.create(custom_id=custom_id, order_id=order_id, symbol=symbol, side=t_side, volume=volume, trade_type=account.type, account=account)
    return trade

def get_trade(custom_id, symbol, side, account):
    t_side = "B" if str.lower(side) == "buy" else "S"

    trade = CryptoTradeDetails.objects.filter(custom_id=custom_id, symbol=symbol, side=t_side, account=account).first()
    return trade

def update_trade_after_close(trade, closed_volume, price):
    trade.exit_price = price
    trade.remaining_volume = trade.volume - closed_volume
    trade.status = 'P'
    trade.save()

    return trade
