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
                trade_details = get_trade_info_by_id(tl, position_id, order_id)
                print('trade_details', trade_details)
                order_id = position_id
                # entry_price = trade_details.get('entry_price')  # Adjust the key based on API response structure
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': order_id,
                'symbol': symbol,
                'price': None,
                'qty': trade_details.get('qty', quantity),
            }
        else:
            return {'error': "Failed to open trade."}
    except Exception as e:
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
        positions = tl.get_all_positions()  # Assuming this returns a pandas DataFrame
        # orders = tl.get_all_orders(history=True)

        # print('orders', orders) 

        if 'id' not in positions.columns:
            print("Column 'orderId' not found in orders")
            return None

        # Locate the row matching the trade ID
        trade_info = positions.loc[positions['id'] == int(position_id)]

        if not trade_info.empty:
            # Extract relevant trade details (assuming these columns exist in the DataFrame)
            trade_details = {
                'qty': trade_info['qty'].values[0].item(),
                # 'price': trade_info['price'].values[0],
                # 'quantity': trade_info['quantity'].values[0],
                # 'side': trade_info['side'].values[0],
                # 'status': trade_info['status'].values[0],
                # 'timestamp': trade_info['timestamp'].values[0]
            }
            return trade_details
        else:
            return None
    except Exception as e:
        print("An error occurred:", str(e))
        return None


def get_trade_data(tl, order_id):
    trades = tl.get_all_executions()
    orders_history = tl.get_all_orders(history=True)

    matching_orders = orders_history[orders_history["id"] == order_id]
    if len(matching_orders) == 0:
        return None
    
    position_id = int(matching_orders["positionId"].iloc[0])
    return position_id


    return matching_orders

