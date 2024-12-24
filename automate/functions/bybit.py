import time
import hmac
import hashlib
import requests

BYBIT_API_URL = 'https://api.bybit.com'

def create_bybit_signature(api_key, secret_key, params):
    """Create Bybit signature using HMAC SHA256."""
    sorted_params = sorted(params.items())
    query_string = '&'.join(f"{key}={value}" for key, value in sorted_params)
    signature = hmac.new(
        secret_key.encode('utf-8'), 
        query_string.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()
    return signature

def send_bybit_request(method, endpoint, api_key, secret_key, params=None):
    """Send authenticated requests to the Bybit API."""
    if params is None:
        params = {}
    params['api_key'] = api_key
    params['timestamp'] = str(int(time.time() * 1000))
    params['sign'] = create_bybit_signature(api_key, secret_key, params)

    url = f"{BYBIT_API_URL}{endpoint}"
    if method.upper() == 'GET':
        response = requests.get(url, params=params)
    else:
        response = requests.post(url, data=params)
    return response.json()

def check_bybit_credentials(api_key, secret_key, account_type="S"):
    """
    Check Bybit account credentials.
    account_type: "SPOT" for Spot account, "CONTRACT" for Futures account
    """
    try:
        endpoint = '/v2/private/wallet/balance'
        if account_type.upper() == "S":
            endpoint = '/spot/v1/account'

        params = {}
        response = send_bybit_request('GET', endpoint, api_key, secret_key, params)
        print(account_type, response)
        if 'ret_code' in response and response['ret_code'] != 0:
            return {'error': response.get('ret_msg', 'Unknown error'), "valid": False}
        return {'message': "API credentials are valid.", "valid": True, "data": response}
    except Exception as e:
        return {'error': str(e)}
