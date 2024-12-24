import time
import hmac
import hashlib
import requests


API_URL = 'https://api.binance.us'


def create_signature(query_string, secret):
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()


def send_request(method, endpoint, api_key, api_secret, params={}):
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    timestamp = int(time.time() * 1000)
    query_string += f"&timestamp={timestamp}"
    signature = create_signature(query_string, api_secret)
    headers = {
        'X-MBX-APIKEY': api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    url = f"{API_URL}{endpoint}?{query_string}&signature={signature}"
    response = requests.request(method, url, headers=headers)
    return response.json()


def check_binance_us_credentials(api_key, api_secret):
    try:
        response = send_request('GET', '/api/v3/account', api_key, api_secret)
        if response.get('code') == -2014:  # Example error code handling
            return {'error': "Invalid API key or secret.", "valid": False}
        return {'message': "API credentials are valid.", "valid": True}
    except Exception as e:
        return {'error': str(e)}


def get_account_balance(account, asset):
    """Fetch the available balance for a specific asset."""
    response = send_request('GET', '/api/v3/account', account.apiKey, account.secretKey)
    balances = {item['asset']: float(item['free']) for item in response['balances']}
    return balances.get(asset, 0)


def adjust_trade_quantity(account, symbol, quote_order_qty, trade_type):
    """Adjust the trade quantity based on available balance."""
    try:
        base_asset, quote_asset = symbol[:-4], symbol[-4:]  # Assumes symbols are like BTCUSDT
        if trade_type.upper() == "BUY":
            pass
            # available_balance = get_account_balance(account, quote_asset)
            # print("Available balance:", available_balance)
            # if available_balance < quote_order_qty:
            #     return available_balance  # Use the maximum available balance
        elif trade_type.upper() == "SELL":
            available_balance = get_account_balance(account, base_asset)

            print("Available balance:", available_balance)
            # current_price = get_asset_price(symbol)
            # max_sellable_qty = available_balance * current_price
            if available_balance < quote_order_qty:
                return available_balance  # Use the maximum sellable amount
        return quote_order_qty
    except Exception as e:
        print('adjust trade quantity error: ', str(e))
        return quote_order_qty


def open_binance_us_trade(account, symbol, side, quantity, custom_id):
    try:
        adjusted_quantity = adjust_trade_quantity(account, symbol, float(quantity), side)

        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": adjusted_quantity,
            # "quoteOrderQty": adjusted_quantity
        }

        print("Quantity:", quantity, "Qty:", adjusted_quantity)

        response = send_request('POST', '/api/v3/order', account.apiKey, account.secretKey, params)

        if response.get('msg') is not None:
            raise Exception(response.get('msg'))
        return {
            'message': f"Trade opened with order ID {response.get('orderId')}.",
            'order_id': response.get('orderId'),
            'symbol': response.get('symbol', symbol),
            'price': response['fills'][0]['price'],
            'qty': adjusted_quantity,
        }
    except Exception as e:
        return {'error': str(e)}


def close_binance_us_trade(account, symbol, side, quantity):
    t_side = "SELL" if side.upper() == "BUY" else "BUY"
    try:
        adjusted_quantity = adjust_trade_quantity(account, symbol, float(quantity), t_side)

        params = {
            "symbol": symbol,
            "side": t_side,
            "type": "MARKET",

            "quantity": adjusted_quantity
            # "quoteOrderQty": adjusted_quantity
        }

        print("Quantity:", quantity, "Qty:", adjusted_quantity)

        response = send_request('POST', '/api/v3/order', account.apiKey, account.secretKey, params)

        if response.get('msg') is not None:
            raise Exception(response.get('msg'))

        return {
            'message': f"Trade closed for order ID {response.get('orderId')}.",
            "id": response.get('orderId'),
            'price': response['fills'][0]['price'],
        }
    except Exception as e:        
        return {'error': str(e)}


def get_asset_price(symbol):
    url = API_URL + "/api/v3/ticker/price"
    response = requests.get(url, params={"symbol": symbol})
    response.raise_for_status()
    price_data = response.json()
    return float(price_data["price"])