import re
import time
from automate.functions.alerts_logs_trades import *

from django.db import transaction

def manage_alert(alert_message, account):    
    start = time.perf_counter()
    try:
        print("Webhook request for account #" + str(account.id) + ": " + alert_message)

        alert_data = extract_alert_data(alert_message)
        
        action = alert_data.get('Action')
        custom_id = alert_data.get('ID')

        symbol = alert_data.get('Asset')
        side = alert_data.get('Type')

        partial = alert_data.get('Partial')
        volume = alert_data.get('Volume')

        reverse = alert_data.get('Reverse')

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
            if reverse:
                custom_id = f"{custom_id}R{reverse}"
                trades_to_close = get_previous_trade(custom_id, symbol, side, account, strategy_id, reverse)

            trade, closed_trades = open_trade_by_account(account, symbol, side, volume, custom_id, trades_to_close if reverse else [])

            for closed_trade in closed_trades:
                end_exe_ct = closed_trade.get('end_exe', None)
                orig_trade = closed_trade.get('orig_trade')
                closed_volume = closed_trade.get('qty', orig_trade.remaining_volume)
                rtrade = update_trade_after_close(orig_trade, closed_volume, closed_trade)
                save_log("S", alert_message, f'Opposite order with ID {closed_trade.get("order_id")} was closed successfully due to reverse signal.', account, start, end_exe_ct, rtrade)

            end_exe = trade.get('end_exe', None)
            # print('Trade:', trade)
            if trade.get('error') is not None:
                raise Exception(trade.get('error'))
            saved_trade = save_new_trade(custom_id, symbol, side, trade, account, strategy_id)
            save_log("S", alert_message, f'Order with ID {trade.get('order_id')} was placed successfully.', account, start, end_exe, saved_trade)

        elif action == 'Exit':
            trade_to_close = get_trade_for_update(custom_id, symbol, side, account, strategy_id)
            if not trade_to_close:
                raise Exception(f"No trade found to close with ID: {custom_id}")

            volume_close = volume_to_close(trade_to_close, partial)
            closed_trade = close_trade_by_account(account, trade_to_close, symbol, side, volume_close)

            end_exe = closed_trade.get('end_exe', None)

            if closed_trade.get('error') is not None:
                raise Exception(closed_trade.get('error'))
            
            closed_volume = closed_trade.get('qty', volume_close)

            trade = update_trade_after_close(trade_to_close, closed_volume, closed_trade)
            save_log("S", alert_message, f'Order with ID {trade_to_close.order_id} was closed successfully.', account, start, end_exe, trade)

    except Exception as e:   
        print('API Error: %s' % e)
        save_log("E", alert_message, str(e), account, latency_start=start)
        return {"error": str(e)}


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
            data['Type'] = str(value).upper()
        elif key == 'X':
            data['Action'] = 'Exit'
            data['Type'] = str(value).upper()
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

        elif key == 'R':
            data['Reverse'] = value
        
    
    return data
