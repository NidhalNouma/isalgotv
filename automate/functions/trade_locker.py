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
            return {'message': f"Trade opened with order ID {order_id}.", 'order_id': order_id}
        else:
            return {'error': "Failed to open trade."}
    except Exception as e:
        return {'error': str(e)}

def close_tradelocker_trade(account, id, quantity):
    try:
        # Close the position associated with the given order ID

        tl = TLAPI(environment=get_tradelocker_base_url(account.type), username=account.username, password=account.password, server=account.server)
        result = tl.close_position(position_id = int(id), close_quantity = 0)
        if result:
            return {'message': f"Trade closed for order ID {id}."}
        else:
            return {'error': "Failed to close trade."}
    except Exception as e:
        return {'error': str(e)}