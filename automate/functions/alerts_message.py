import re
from .alerts_logs_trades import *

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

        strategy_id = alert_data.get('strategy_ID', None)

        symbol = adjust_symbol_name(account, symbol)

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
            # print('Trade:', trade)
            if trade.get('error') is not None:
                raise Exception(trade.get('error'))
            saved_trade = save_new_trade(custom_id, side, trade, account, strategy_id)
            save_log("S", alert_message, f'Order with ID {trade.get('order_id')} was placed successfully.', account, saved_trade)

        elif action == 'Exit':
            trade_to_close = get_trade(custom_id, symbol, side, account, strategy_id)
            if not trade_to_close:
                raise Exception(f"No trade found to close with ID: {custom_id}")

            volume_close = volume_to_close(trade_to_close, partial)
            closed_trade = close_trade_by_account(account, trade_to_close, symbol, side, volume_close)

            if closed_trade.get('error') is not None:
                raise Exception(closed_trade.get('error'))
            
            closed_volume = closed_trade.get('qty', volume_close)

            trade = update_trade_after_close(trade_to_close, closed_volume, closed_trade)
            save_log("S", alert_message, f'Order with ID {trade_to_close.order_id} was closed successfully.', account, trade)

    except Exception as e:   
        print('API Error: %s' % e)
        save_log("E", alert_message, str(e), account)
        return {"error": str(e)}

def adjust_symbol_name(account, _symbol:str):
    symbol = _symbol

    if account.broker_type == 'binance' and account.type == "C":
        if not symbol.endswith("_PERP"):
            symbol = symbol + "_PERP"

    if account.broker_type == 'kucoin' and account.type != "S":
            symbol = symbol.replace('-', '')
            if not symbol.endswith('M'):
                symbol = symbol + 'M'
            
    if account.broker_type == 'bingx' or account.broker_type == 'kucoin' or account.broker_type == 'coinbase':
        symbol = symbol.replace("/", "-")
        if '-' not in symbol:
            if symbol.endswith('USDT'):
                symbol = symbol[:-4] + '-USDT'
            elif symbol.endswith('USDC'):
                symbol = symbol[:-4] + '-USDC'
            elif symbol.endswith('BTC'):
                symbol = symbol[:-3] + '-BTC'
            elif symbol.endswith('ETH'):
                symbol = symbol[:-3] + '-ETH'
            elif symbol.endswith('DAI'):
                symbol = symbol[:-3] + '-DAI'
            elif symbol.endswith('USD'):
                symbol = symbol[:-3] + '-USD'
            elif symbol.endswith('EUR'):
                symbol = symbol[:-3] + '-EUR'
            elif symbol.endswith('GBP'):
                symbol = symbol[:-3] + '-GBP'
    
    if account.broker_type == 'coinbase':
        symbol = symbol.replace(" ", "-")
        # Remove leading dash if present
        if symbol.startswith('-'):
            symbol = symbol[1:]

        if account.type == 'P':
            if symbol.endswith('PERP'):
                if '-' not in symbol:
                    symbol = symbol[:-4] + '-PERP'

                symbol = symbol + '-INTX'
            else:
                symbol = symbol + '-PERP-INTX'

        elif account.type == 'F':
            symbol = symbol + '-CDE'


    
    return symbol


def extract_alert_data(alert_message):
    data = {}

    """
    Splits strings like:
        "D=BUY A=BTC-PERP INTX V=10 NUM=4 ST=1"
    into:
        ["D=BUY", "A=BTC-PERP INTX", "V=10", "NUM=4", "ST=1"]
    """
    pattern = r'([A-Z]+=.*?)(?=\s+[A-Z]+=|$)'
    parts = re.findall(pattern, alert_message)
    
    # Extract other fields from the message
    for part in parts:
        key, value = [x.strip() for x in part.split('=', 1)]
        key = str(key).upper()
        
        if key == 'D':
            data['Action'] = 'Entry'
            data['Type'] = value
        elif key == 'X':
            data['Action'] = 'Exit'
            data['Type'] = value
        elif key == 'A':
            data['Asset'] = str(value).upper()
        elif key == 'V':
            data['Volume'] = value
        elif key == 'P':
            data['Partial'] = value
        elif key == 'ID' or key == 'NUM':
            data['ID'] = value
        elif key == 'ST' or key == 'ST_ID' or key == "SR":
            data['strategy_ID'] = value
    
    return data
