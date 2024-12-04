import time
import hmac
import hashlib
import requests
import base64

API_URL = 'https://api.bitget.com'

def create_signature(timestamp, method, request_path, secret_key, body=''):
    message = timestamp + method.upper() + request_path + body
    return base64.b64encode(hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()).decode()

def send_request(method, endpoint, api_key, secret_key, passphrase, body=None):
    timestamp = str(int(time.time() * 1000))
    headers = {
        'ACCESS-KEY': api_key,
        'ACCESS-SIGN': create_signature(timestamp, method, endpoint, secret_key, body or ''),
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    url = f"{API_URL}{endpoint}"
    if method.upper() == 'GET':
        response = requests.get(url, headers=headers)
    else:
        response = requests.post(url, headers=headers, json=body)
    return response.json()

def check_bitget_credentials(api_key, secret_key, passphrase, trade_type="S"):
    try:
        endpoint = '/api/spot/v1/account/accounts'
        if trade_type == "F":
            endpoint = '/api/mix/v1/account/accounts'

        response = send_request('GET', endpoint, api_key, secret_key, passphrase)
        if 'code' in response and response['code'] != '0':
            return {'error': response['msg'], "valid": False}
        return {'message': "API credentials are valid.", "valid": True}
    except Exception as e:
        return {'error': str(e)}

def open_bitget_trade(account, symbol, side, quantity):
    try:
        endpoint = '/api/spot/v1/orders'
        if account.type == "F":
            endpoint = '/api/mix/v1/order/placeOrder'
            
        body = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity
        }
        response = send_request('POST', endpoint, account.apiKey, account.secretKey, account.pass_phrase, body)
        return response
    except Exception as e:
        return {'error': str(e)}

def close_bitget_trade(account, symbol, side, quantity):
    opposite_side = "sell" if side.lower() == "buy" else "buy"
    try:
        endpoint = '/api/spot/v1/orders'
        if account.type == "F":
            endpoint = '/api/mix/v1/order/placeOrder'
        body = {
            "symbol": symbol,
            "side": opposite_side.upper(),
            "type": "MARKET",
            "quantity": quantity
        }
        response = send_request('POST', endpoint, account.apiKey, account.secretKey, account.pass_phrase, body)
        return response
    except Exception as e:
        return {'error': str(e)}