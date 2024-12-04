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

def open_binance_us_trade(api_key, api_secret, symbol, side, quantity):
    try:
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity
        }
        response = send_request('POST', '/api/v3/order', api_key, api_secret, params)
        return response
    except Exception as e:
        return {'error': str(e)}

def close_binance_us_trade(api_key, api_secret, symbol, side, quantity):
    t_side = "SELL" if side == "BUY" else "BUY"
    try:
        params = {
            "symbol": symbol,
            "side": t_side,
            "type": "MARKET",
            "quantity": quantity
        }
        response = send_request('POST', '/api/v3/order', api_key, api_secret, params)
        return response
    except Exception as e:
        return {'error': str(e)}