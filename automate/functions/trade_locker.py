from tradelocker import TLAPI

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
                trade_details = get_trade_info_by_id(tl, order_id)
                # entry_price = trade_details.get('entry_price')  # Adjust the key based on API response structure
                return {
                    'message': f"Trade opened with order ID {position_id}.",
                    'order_id': position_id,
                    'price': 12
                }
        else:
            return {'error': "Failed to open trade."}
    except Exception as e:
        return {'error': str(e)}

def close_tradelocker_trade(account, id, quantity):
    try:
        tl = TLAPI(environment=get_tradelocker_base_url(account.type), username=account.username, password=account.password, server=account.server)
        trade_details = get_trade_info_by_id(tl, id)
        if not trade_details:
            return {'error': f"Trade details not found for order ID {id}."}
        
        result = tl.close_position(order_id = int(id), close_quantity = float(quantity))


        return {'message': f"Trade closed for order ID {id}.", id: id}
    
    except Exception as e:
        return {'error': str(e)}
    

def get_trade_info_by_id(tl, trade_id):
    orders = tl.get_all_positions()  # Assuming this returns a pandas DataFrame
    # print('orders', orders) 

    if 'id' not in orders.columns:
        print("Column 'orderId' not found in orders")
        return None

    # Locate the row matching the trade ID
    trade_info = orders.loc[orders['id'] == int(trade_id)]

    # print('info', trade_info)

    if not trade_info.empty:
        # Extract relevant trade details (assuming these columns exist in the DataFrame)
        trade_details = {
            'symbol': trade_info['symbol'].values[0],
            'price': trade_info['price'].values[0],
            'quantity': trade_info['quantity'].values[0],
            'side': trade_info['side'].values[0],
            'status': trade_info['status'].values[0],
            'timestamp': trade_info['timestamp'].values[0]
        }
        return trade_details
    else:
        return None