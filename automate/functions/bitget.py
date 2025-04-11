import time
import hmac
import hashlib
import requests
import base64
import json
from decimal import Decimal, ROUND_DOWN

API_URL = 'https://api.bitget.com'

def create_signature(timestamp, method, request_path, secret_key, body=''):
    if isinstance(body, dict):
        body = json.dumps(body)

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
        endpoint = '/api/v2/spot/account/info'
        if trade_type == "U":
            endpoint = '/api/v2/mix/account/accounts?productType=USDT-FUTURES'
        elif trade_type == "C":
            endpoint = '/api/v2/mix/account/accounts?productType=COIN-FUTURES'
        elif trade_type == "US":
            endpoint = '/api/v2/mix/account/accounts?productType=USDC-FUTURES'

        response = send_request('GET', endpoint, api_key, secret_key, passphrase)
        print(trade_type, response)
        if 'code' in response and int(response['code']) != 0:
            return {'error': response['msg'], "valid": False}
        return {'message': "API credentials are valid.", "valid": True}
    except Exception as e:
        return {'error': str(e)}

def open_bitget_trade(account, symbol, side, quantity, oc = 'open'):
    try:
        # Endpoint for placing an order
        endpoint = '/api/v2/spot/trade/place-order'
        order_endpoint = '/api/v2/spot/trade/orderInfo'
        data_endpoint = f"/api/v2/spot/market/tickers?symbol={symbol}"
        decimals_endpoint = f"/api/v2/spot/public/symbols?symbol={symbol}"

        if account.type == "U":
            productType = "USDT-FUTURES"
            endpoint = '/api/v2/mix/order/place-order'
            order_endpoint = '/api/v2/mix/order/detail'
            data_endpoint = f"/api/v2/mix/market/ticker?symbol={symbol}&productType={productType}"
            decimals_endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"

        elif account.type == "C":
            productType = "COIN-FUTURES"
            endpoint = '/api/v2/mix/order/place-order'
            order_endpoint = '/api/v2/mix/order/detail'
            data_endpoint = f"/api/v2/mix/market/ticker?symbol={symbol}&productType={productType}"
            decimals_endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"

        elif account.type == "UC":
            productType = "USDC-FUTURES"
            endpoint = '/api/v2/mix/order/place-order'
            order_endpoint = '/api/v2/mix/order/detail'
            data_endpoint = f"/api/v2/mix/market/ticker?symbol={symbol}&productType={productType}"
            decimals_endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"

        precisions = send_request('GET', decimals_endpoint, account.apiKey, account.secretKey, account.pass_phrase)
        
        market_data = send_request('GET', data_endpoint, account.apiKey, account.secretKey, account.pass_phrase)
        
        if "msg" in market_data and market_data.get('code') != '00000':
            raise Exception(response.get('msg'))
        
        if not market_data or 'data' not in market_data or not market_data['data']:
             raise ValueError("Market data is missing or invalid")

        current_price = float(market_data['data'][0].get('lastPr', 1))

        # Adjust quantity if opening a BUY order with base coin
        decimals = precisions['data'][0].get('quotePrecision', 1)
        if precisions['data'][0].get('quotePrecision', None) is None:
           decimals = precisions['data'][0].get('volumePlace', 1) 

        if side.upper() == "BUY" and account.type == "S":
            formatted_quantity = f"{float(quantity) * current_price:.{decimals}f}"
            quantity = float(formatted_quantity)
        else:            
            formatted_quantity = f"{float(quantity):.{decimals}f}"
            quantity = float(formatted_quantity)
        

        body = {
            "symbol": symbol,
            "side": side.upper(),
            "orderType": "MARKET",
            "size": quantity  # Ensure this is the base coin amount
        }

        if account.type != 'S':
            body["productType"] = productType
            body["marginMode"] = "isolated"
            body["marginCoin"] = "USDT"
            body["tradeSide"] = oc

        print("body ==> ", body)

        # Send the trade request
        response = send_request('POST', endpoint, account.apiKey, account.secretKey, account.pass_phrase, body)


        if "msg" in response and response.get('code') != '00000':
            raise Exception(response.get('msg'))
        
        # Extract order details
        order_id = response["data"].get("orderId")
        order_url = order_endpoint + f"?orderId={order_id}"

        if account.type != 'S':
            order_url += f"&productType={productType}&symbol={symbol}"

        data = send_request('GET', order_url, account.apiKey, account.secretKey, account.pass_phrase)
        data = data.get('data')

        print("trade data => ", data)
        
        if data is None:
            raise ValueError("No data found in response")

        # Distinguish handling based on account type
        if account.type == 'S':
            # Expecting a list and taking the first item
            if isinstance(data, list) and data:
                order_data = data[0]
            else:
                raise TypeError("Expected data as list for type 'S'")
        else:
            # Directly use the dictionary
            if isinstance(data, dict):
                order_data = data
            else:
                raise TypeError("Expected data as dict for other account types")


        o_size = order_data.get("baseVolume", 0)
        if account.type != 'S':
            o_size = order_data.get("size", 0)

        if o_size == 0:
            o_size = quantity

        o_price = order_data.get("price", 0) 

        if not o_price or o_price == 0:
            o_price = current_price

        return {
            "order_id": order_id, 
            "symbol": order_data.get("symbol", symbol),
            "side": side,
            "price": o_price,
            "qty": o_size,
        }
    
    except Exception as e:
        print('error opening bitget trade: ', str(e))
        return {'error': str(e)}

def close_bitget_trade(account, symbol, side, quantity):
    if account.type == "S":
        opposite_side = "sell" if side.lower() == "buy" else "buy"
    else:
        opposite_side = side.lower()
    try:
        trade = open_bitget_trade(account, symbol, opposite_side, quantity, oc = 'close')
        if trade.get('error') is not None:
            raise Exception(trade.get('error'))
        return trade
    except Exception as e:
        return {'error': str(e)}