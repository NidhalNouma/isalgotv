import time
import hmac
import hashlib
import requests
import json
from datetime import datetime

BYBIT_API_URL = 'https://api.bybit.com/v5'

# def send_bybit_request(method, endpoint, api_key, secret_key, params=None):
#     """Send authenticated requests to the Bybit API."""
#     if params is None:
#         params = {}
#     params['api_key'] = api_key
#     params['timestamp'] = str(int(time.time() * 1000))
#     params['sign'] = create_bybit_signature(api_key, secret_key, params)

#     url = f"{BYBIT_API_URL}{endpoint}"
#     if method.upper() == 'GET':
#         response = requests.get(url, params=params)
#     else:
#         response = requests.post(url, data=params)
#     return response.json()

# def check_bybit_credentials(api_key, secret_key, account_type="S"):
#     """
#     Check Bybit account credentials.
#     account_type: "SPOT" for Spot account, "CONTRACT" for Futures account
#     """
#     try:
#         endpoint = '/v2/private/wallet/balance'
#         if account_type.upper() == "S":
#             endpoint = '/spot/v1/account'

#         params = {}
#         response = send_bybit_request('GET', endpoint, api_key, secret_key, params)
#         print(account_type, response)
#         if 'ret_code' in response and response['ret_code'] != 0:
#             return {'error': response.get('ret_msg', 'Unknown error'), "valid": False}
#         return {'message': "API credentials are valid.", "valid": True, "data": response}
#     except Exception as e:
#         return {'error': str(e)}

def create_bybit_signature(api_secret, params):
    """Create the signature for a Bybit API request."""
    sorted_params = sorted(params.items())
    query_string = '&'.join(f"{key}={value}" for key, value in sorted_params)
    signature = hmac.new(
        api_secret.encode('utf-8'), 
        query_string.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()
    return signature

def send_bybit_request(method, endpoint, api_key, api_secret, params):
    """Send a request to the Bybit API."""
    params['api_key'] = api_key
    params['timestamp'] = str(int(time.time() * 1000))
    params['sign'] = create_bybit_signature(api_secret, params)
    
    url = f"{BYBIT_API_URL}{endpoint}"
    if method.upper() == 'GET':
        response = requests.get(url, params=params)
    else:
        response = requests.post(url, json=params)
    return response.json()

def check_bybit_credentials(api_key, api_secret, account_type="S"):
    """Check the validity of the Bybit API credentials."""
    try:
        params = {
            'accountType': 'UNIFIED'
        }
        endpoint = '/account/wallet-balance'
        response = send_bybit_request('GET', endpoint, api_key, api_secret, params)
        if response['retCode'] != 0:
            return {'error': response['retMsg'], 'valid': False}
        return {'message': "API credentials are valid.", 'valid': True}
    except Exception as e:
        return {'error': str(e)}

def open_bybit_trade(account, symbol, side, quantity):
    """Place a market order on Bybit."""
    try:
        if account.type == "S":
            category = 'spot'
        else:
            category = 'linear'

        params = {
            'symbol': symbol,
            'category': category,
        }
        precision_req = send_bybit_request('GET', '/market/instruments-info', account.apiKey, account.secretKey, params)
        # print(precision_req)

        if category == 'linear':
            precison = precision_req['result']['list'][0]['lotSizeFilter']['qtyStep']
        else:
            precison = precision_req['result']['list'][0]['lotSizeFilter']['basePrecision']

        base_coin = precision_req['result']['list'][0]['baseCoin']

        if account.type == "S":
            balance = getAssetBalance(account, base_coin)
            if float(balance) < float(quantity):
                quantity = balance

        if precison is not None:
            decimal_places = len(str(precison).split('.')[1]) if '.' in str(precison) else 0

            formatted_quantity = f"{float(quantity):.{decimal_places}f}"
            quantity = float(formatted_quantity)

        params = {
            'symbol': symbol,
            'category': category,
        }
        price_req = send_bybit_request('GET', '/market/tickers', account.apiKey, account.secretKey, params)
        price = price_req['result']['list'][0]['lastPrice']

        endpoint = '/order/create'
        params = {
            'symbol': symbol,
            'side': side.capitalize(),
            'order_type': 'Market',
            'qty': str(quantity),
            
            'category': category,

            'marketUnit': 'baseCoin',
            'time_in_force': 'IOC'
        }
        print(params)
        response = send_bybit_request('POST', endpoint, account.apiKey, account.secretKey, params)

        # print(response)
        if response['retCode'] != 0:
            raise Exception(response['retMsg'])
        
        order_id = response['result']['orderId']

        params = {
            'orderId': order_id,
            'symbol': symbol,
            'side': side.upper(),
            'category': category,
        }
        order = send_bybit_request('GET', '/order/history', account.apiKey, account.secretKey, params)
        # print(order)
        
        if len(order['result']['list']) > 0:
            qty = order['result']['list'][0]['qty']
        else:
            qty = quantity
        
        return {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'price': price,
            'qty': qty
        }
    except Exception as e:
        return {'error': str(e)}

def close_bybit_trade(account, symbol, side, quantity):
    """Close a trade on Bybit."""
    opposite_side = 'Sell' if side == 'Buy' else 'Buy'
    return open_bybit_trade(account, symbol, opposite_side, quantity)

def getAssetBalance(account, coin):
    """Get the balance of a specific asset on Bybit."""
    try:
        params = {
            'accountType': 'UNIFIED',
            'coin': coin
        }
        endpoint = '/account/wallet-balance'
        response = send_bybit_request('GET', endpoint, account.apiKey, account.secretKey, params)
        # print('coin', response)
        if response['retCode'] != 0:
            raise Exception(response['retMsg'])
        
        b = '0'
        for balance in response['result']['list'][0]['coin']:
            if balance['coin'] == coin:
                b = balance['walletBalance']
        return b
    except Exception as e:
        raise Exception(e)