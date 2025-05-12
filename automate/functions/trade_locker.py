from tradelocker import TLAPI
import requests
from datetime import datetime
from django.utils import timezone

def get_tradelocker_base_url(type = 'L'):
    if type == 'L':
        return "https://live.tradelocker.com"
    return "https://demo.tradelocker.com"

def check_tradelocker_credentials(username, password, server, type):
    try:
        # Initialize the API client
        tl = TLAPI(environment=get_tradelocker_base_url(type), username=username, password=password, server=server)
        accounts = tl.get_all_accounts()
        if len(accounts) > 0:
            return {'message': "API credentials are valid.", "valid": True}
        else:
            return {'error': "Failed to retrieve accounts.", "valid": False}
    except Exception as e:
        return {'error': str(e), "valid": False}

def open_tradelocker_trade(account, symbol, side, quantity):
    try:
        # Fetch the instrument ID for the given symbol
        tl = TLAPI(environment=get_tradelocker_base_url(account.type), username=account.username, password=account.password, server=account.server)
        instrument_id = tl.get_instrument_id_from_symbol_name(symbol)
        if not instrument_id:
            return {'error': f"Symbol {symbol} not found."}
        # Create a market order
        order_id = tl.create_order(instrument_id, quantity=quantity, side=side.lower(), type_="market")
        
        if order_id:
            position_id = tl.get_position_id_from_order_id(order_id)
            if position_id:
                trade_details = get_trade_info_by_id(tl, position_id, order_id)
                
                # print(trade_details)

                if trade_details is None:
                    raise Exception('Trade has been executed but Position was not found')
                order_id = position_id

                account_info = tl.get_trade_accounts()
                # print(account_info)
                currency = account_info[0].get('currency', '')
                return {
                    'message': f"Trade opened with order ID {order_id}.",
                    'order_id': order_id,
                    'symbol': symbol,
                    'qty': trade_details.get('qty', quantity),
                    'price': trade_details.get('price', 0),
                    'time': trade_details.get('time', timezone.now()),
                    'fees': trade_details.get('fees', 0),
                    'currency': currency if currency else '',
                }
        else:
            return {'error': "Failed to open trade."}
    except Exception as e:
        print("Error:", e)
        return {'error': str(e)}

def close_tradelocker_trade(account, id, quantity):
    try:
        if(float(quantity) < 0.01):
            raise ValueError("Quantity must be greater than 0.01.")
        
        tl = TLAPI(environment=get_tradelocker_base_url(account.type), username=account.username, password=account.password, server=account.server)
        result = tl.close_position(position_id = int(id), close_quantity = float(quantity))
        # trade_details = get_trade_info_by_id(tl, id)
        return {
            'message': f"Trade closed for order ID {id}.", 
            "id": id,
            'qty': quantity,
            }
    
    except Exception as e:
        print("An error occurred:", str(e))
        return {'error': str(e)}
    

def get_trade_info_by_id(tl, position_id, order_id):
    try:
        positions = tl.get_all_positions()

        if 'id' not in positions.columns:
            print("Column 'orderId' not found in orders")
            return None

        # Locate the row matching the trade ID
        trade_info = positions.loc[positions['id'] == int(position_id)]

        # # Print each column name and its corresponding value for the single row
        # if not trade_info.empty:
        #     row = trade_info.iloc[0]
        #     for col in trade_info.columns:
        #         print(f"{col}: {row[col]}")
        # else:
        #     print("No trade info found")

        if not trade_info.empty:
            row = trade_info.iloc[0]
            
            raw_ts = row['openDate']
            # Assume timestamp is in milliseconds
            dt_naive = datetime.fromtimestamp(raw_ts / 1000.0)
            time_dt = timezone.make_aware(dt_naive, timezone.utc)
            # Extract relevant trade details (assuming these columns exist in the DataFrame)
            trade_details = {
                'qty': str(trade_info['qty'].values[0].item()),
                'price': str(trade_info['avgPrice'].values[0].item()),
                'side': row['side'],
                'time': time_dt,
                'fees': str(row.get('fee', 0)),
            }
            return trade_details
        else:
            return None
    except Exception as e:
        print("An error occurred:", str(e))
        return None

def get_closed_orders_by_position_id(tl, position_id, entry_time):
    try:

        dt = entry_time

        # Make sure it's in UTC
        if timezone.is_naive(dt):
            # if your `USE_TZ=True` you’ll usually get an aware datetime from Django,
            # but if not:
            dt = timezone.make_aware(dt, timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        ts_ms = int(dt.timestamp() * 1000)
        
        orders_history = tl.get_all_orders(history=True, start_timestamp=ts_ms)
        # Filter orders for this position_id
        if not orders_history.empty:
            records = orders_history.to_dict(orient="records")
            # Filter for the given position_id
            matches = [rec for rec in records if str(rec.get("positionId")) == position_id]
            # Sort so the most recent (highest timestamp) comes first
            matches.sort(key=lambda r: r.get('lastModified', 0), reverse=True)
            return matches
        
        return []
    except Exception as e:
        return None


def get_closed_trades(tl, position_id = None, entry_time = None):
    try:
        route_url = f"{tl.get_base_url()}/trade/reports/close-trades-history"
        headers = tl._get_headers()

        ts_ms = 0
        if entry_time:
            dt = entry_time

            # Make sure it's in UTC
            if timezone.is_naive(dt):
                # if your `USE_TZ=True` you’ll usually get an aware datetime from Django,
                # but if not:
                dt = timezone.make_aware(dt, timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)

            ts_ms = int(dt.timestamp() * 1000)

        params = {
            # 'from': ts_ms,
        }

        response = requests.get(url=route_url, params=params, headers=headers, timeout=tl._TIMEOUT)
        response_json = tl._get_response_json(response)

        data = response_json.get('data', [])

        # print(data)
        if not position_id:
            return data
        else:

            matches = [rec for rec in data if str(rec.get("positionId")) == position_id]
            matches.sort(key=lambda r: r.get('closeMilliseconds', 0), reverse=True)
            return matches
    except Exception as e:
        return None


def get_tradelocker_trade_data(account, trade):

    tl = TLAPI(environment=get_tradelocker_base_url(account.type), username=account.username, password=account.password, server=account.server)
    closed_positions = get_closed_trades(tl, trade.order_id, trade.entry_time)

    last_position = closed_positions[0] if closed_positions else None

    if last_position:
        # print(last_position)

        raw_ts = last_position.get('closeMilliseconds', 0)
        # Assume timestamp is in milliseconds
        dt_naive = datetime.fromtimestamp(int(raw_ts) / 1000.0)
        time_dt = timezone.make_aware(dt_naive, timezone.utc)

        res = {
            'volume': str(last_position.get('closeAmount', '')),
            'side': str(trade.side),

            'open_price': str(trade.entry_price),
            'close_price': str(last_position.get('closePrice')),

            'open_time': str(trade.entry_time),
            'close_time': str(time_dt), 

            'fees': str(float(last_position.get('commission') or 0) + float(last_position.get('swap') or 0)), 
            'profit': str(last_position.get('profit')),

            'commission': str(last_position.get('commission')),
            'swap': str(last_position.get('swap')),

        }

        return res

    order_history = get_closed_orders_by_position_id(tl, trade.order_id, trade.entry_time)

    last_trade = order_history[0] if order_history else None

    if last_trade:
        # print(last_trade)

        raw_ts = last_trade['lastModified']
        # Assume timestamp is in milliseconds
        dt_naive = datetime.fromtimestamp(raw_ts / 1000.0)
        time_dt = timezone.make_aware(dt_naive, timezone.utc)
        
        res = {
            'volume': str(last_trade.get('qty')),
            'side': str(trade.side),

            'open_price': str(trade.entry_price),
            'close_price': str(last_trade.get('price')),

            'open_time': str(trade.entry_time),
            'close_time': str(time_dt),

        }

        return res

    return None

    


    # return matching_orders
