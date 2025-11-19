import re
import time
from automate.functions.alerts_logs_trades import process_alerts_trades, save_log

def manage_alert(message, account):    
    try:
        start = time.perf_counter()
        alert_messages = str(message).splitlines()

        alerts_data = []

        for alert_message in alert_messages:
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
                
                if side not in ['BUY', 'SELL']:
                    raise Exception("Invalid side value in alert message. Must be 'BUY' or 'SELL'.")

                if not volume and action == 'Entry':
                    raise Exception("No volume found in alert message.")

                if reverse:
                    custom_id = f"{custom_id}R{reverse}"

                alerts_data.append({**alert_data, 'custom_id': custom_id, 'reverse': reverse, 'alert_message': alert_message})

            except Exception as e:   
                print('API Error: %s' % e)
                save_log("E", alert_message, str(e), account, latency_start=start)

        def _partial_val(item):
            p = item.get('Partial')
            if p is None:
                return 0.0
            try:
                s = str(p).strip()
                if s.endswith('%'):
                    s = s[:-1]
                return float(s)
            except Exception:
                return 0.0

        alerts_data.sort(key=lambda x: (0, -_partial_val(x)) if str(x.get('Action', '')).lower() == 'exit' else (1, 0))

        process_alerts_trades(alerts_data, account, start=start)

        return {"status": "completed", "processed_alerts": len(alerts_data), "latency": time.perf_counter() - start}
    except Exception as e:
        print('General Error: %s' % e)
        save_log("E", message, str(e), account, latency_start=start)
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
        elif key == 'V' or key == 'Q':
            expr = str(value).strip()
            try:
                # If the expression ends with %<digits>, separate rounding part
                if '%' in expr:
                    expr, digits = expr.split('%', 1)
                    digits = int(digits) if digits else 0
                else:
                    digits = None

                # Allow only safe characters (numbers, ., *, /)
                if not re.match(r'^[0-9\.\*/\s]+$', expr):
                    raise ValueError(f"Invalid volume expression: {expr}")

                # Safely evaluate the math part
                result = eval(expr)

                # Round if digits were provided
                if digits is not None:
                    result = round(float(result), digits)

                value = result
            except Exception as e:
                raise ValueError(f"Error parsing volume '{value}': {e}")

            data['Volume'] = value
        elif key == 'P':
            data['Partial'] = value
        elif key == 'ID' or key == 'NUM':
            # print('Parsing ID value:', value)
            data['ID'] = value
            id_parts = value.split('.')
            if len(id_parts) > 1:
                for part in id_parts:
                    if part.startswith('Is'):
                        st_id = part.replace('Is', '').strip()
                        data['strategy_ID'] = st_id
        elif key == 'ST' or key == 'ST_ID' or key == "SR":
            data['strategy_ID'] = value

        elif key == 'R':
            data['Reverse'] = value
    print('Extracted alert data:', data)
    return data
