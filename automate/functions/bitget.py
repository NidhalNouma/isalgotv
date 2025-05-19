import time
import hmac
import hashlib
import requests
import base64
import json

from django.utils import timezone
from datetime import datetime
from decimal import Decimal, ROUND_DOWN, ROUND_UP

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
    
def get_exchange_info(account, symbol):
    # Endpoint for placing an order
    endpoint = f"/api/v2/spot/public/symbols?symbol={symbol}"

    if account.type == "U":
        productType = "USDT-FUTURES"
        endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
    elif account.type == "C":
        productType = "COIN-FUTURES"
        endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
    elif account.type == "UC":
        productType = "USDC-FUTURES"
        endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
 
    precisions = send_request('GET', endpoint, account.apiKey, account.secretKey, account.pass_phrase)
    data = precisions['data'][0]
    
    return data
    
def get_exchange_price(account, symbol):
    # Endpoint for placing an order
    endpoint = f"/api/v2/spot/market/tickers?symbol={symbol}"

    if account.type == "U":
        productType = "USDT-FUTURES"
        endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
    elif account.type == "C":
        productType = "COIN-FUTURES"
        endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
    elif account.type == "UC":
        productType = "USDC-FUTURES"
        endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
 
    response = send_request('GET', endpoint, account.apiKey, account.secretKey, account.pass_phrase)
    data = response['data'][0]
    if data.get('lastPr') is None:
        return 0
    price = float(data.get('lastPr'))
    return price


def get_account_balance(account):
    try:
        balances = {}

        endpoint = '/api/v2/spot/account/assets'
        if account.type == "U":
            endpoint = '/api/v2/mix/account/accounts?productType=USDT-FUTURES'
        elif account.type == "C":
            endpoint = '/api/v2/mix/account/accounts?productType=COIN-FUTURES'
        elif account.type == "UC":
            endpoint = '/api/v2/mix/account/accounts?productType=USDC-FUTURES'

        response = send_request('GET', endpoint, account.apiKey, account.secretKey, account.pass_phrase)
        if 'code' in response and int(response['code']) != 0:
            raise ValueError(response['msg'])
        
        for asset in response['data']:
            coin_key = asset.get('coin') or asset.get('marginCoin')
            balances[coin_key] = float(asset.get('available', 0))
            
        return balances
    except Exception as e:
        raise ValueError(str(e))


def adjust_trade_quantity(account, symbol_info, side ,quote_order_qty):
    try:
        base_asset = symbol_info.get('baseCoin')
        quote_asset = symbol_info.get('quoteCoin')

        account_balace = get_account_balance(account)

        base_balance = account_balace.get(base_asset, 0)
        quote_balance = account_balace.get(quote_asset, 0)

        base_decimals = symbol_info.get('quantityPrecision') or symbol_info.get('volumePlace')
        quote_decimals = symbol_info.get('quotePrecision') or symbol_info.get('pricePlace')

        print("Base asset:", base_asset, base_decimals)
        print("Quote asset:", quote_asset, quote_decimals)

        print("Base balance:", base_balance)
        print("Quote balance:", quote_balance)

        try:
            precision = int(base_decimals)
        except (TypeError, ValueError):
            precision = 8  # fallback precision
        quant = Decimal(1).scaleb(-precision)  


        if account.type == "S":  # Spot

            if side.upper() == "BUY":
                if float(quote_balance) <= 0:
                    raise ValueError("Insufficient quote balance.")
                
                price = get_exchange_price(account, symbol_info.get('symbol'))
                if price == 0:
                    raise ValueError("Price is zero, cannot calculate order quantity.")
                # Calculate the maximum order quantity based on the quote balance

                try:
                    precision = int(quote_decimals)
                except (TypeError, ValueError):
                    precision = 8  # fallback precision
                quant = Decimal(1).scaleb(-precision)  

                order_qty = float(quote_order_qty) * price
                qty_dec = Decimal(str(order_qty)).quantize(quant, rounding=ROUND_UP)
                return format(qty_dec, f'.{precision}f')
            
            elif side.upper() == "SELL":
                if float(base_balance) <= 0:
                    raise ValueError("Insufficient base balance.")
                elif float(base_balance) < float(quote_order_qty):
                    # Format quantity to max base_decimals and return as string
                    qty_dec = Decimal(str(base_balance)).quantize(quant, rounding=ROUND_DOWN)
                    return format(qty_dec, f'.{precision}f')
                # Format quantity to max base_decimals and return as string
                qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                return format(qty_dec, f'.{precision}f')
            
            return quote_order_qty
        else:  # Futures

            qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
            return format(qty_dec, f'.{precision}f')

    except Exception as e:
        raise ValueError(str(e))

def open_bitget_trade(account, symbol, side, quantity, oc = 'open'):
    try:
        # Endpoint for placing an order
        endpoint = '/api/v2/spot/trade/place-order'
        if account.type == "U":
            productType = "USDT-FUTURES"
            endpoint = '/api/v2/mix/order/place-order'
        elif account.type == "C":
            productType = "COIN-FUTURES"
            endpoint = '/api/v2/mix/order/place-order'
        elif account.type == "UC":
            productType = "USDC-FUTURES"
            endpoint = '/api/v2/mix/order/place-order'

        sys_info = get_exchange_info(account, symbol)

        if not sys_info:
            raise Exception('Symbol was not found!')
        
        currency_asset = sys_info.get('quoteCoin')
        base_asset = sys_info.get('baseCoin')
        order_symbol = sys_info.get('symbol')

        adjusted_quantity =  adjust_trade_quantity(account, sys_info, side, float(quantity))
        print("Adjusted quantity:", adjusted_quantity)

        if float(adjusted_quantity) <= 0:
            raise ValueError("Insufficient balance for the trade.")

        body = {
            "symbol": order_symbol,
            "side": side.upper(),
            "orderType": "MARKET",
            "size": adjusted_quantity  # Ensure this is the base coin amount
        }

        if account.type == 'U':
            currency_asset = "USDT"
            body["productType"] = productType
            body["marginMode"] = "isolated"
            body["marginCoin"] = currency_asset
            body["tradeSide"] = oc
        elif account.type == 'C':
            currency_asset = "USDE"
            body["productType"] = productType
            body["marginMode"] = "isolated"
            body["marginCoin"] = currency_asset
            body["tradeSide"] = oc
        elif account.type == 'UC':
            currency_asset = "USDC"
            body["productType"] = productType
            body["marginMode"] = "isolated"
            body["marginCoin"] = currency_asset
            body["tradeSide"] = oc

        # print("body ==> ", body)

        # Send the trade request
        response = send_request('POST', endpoint, account.apiKey, account.secretKey, account.pass_phrase, body)

        if "msg" in response and response.get('code') != '00000':
            raise Exception(response.get('msg'))
        
        response = response.get('data')
        order_id = response.get("orderId")

        if order_id is None:
            raise Exception("Order ID not found in response")
        
        order_details = get_order_details(account, order_symbol, order_id)

        if order_details:
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': order_id,
                'closed_order_id': order_id,
                'symbol': symbol,
                "side": side.upper(),
                'qty': order_details.get('volume', adjusted_quantity),
                'price': order_details.get('price', '0'),
                'time': order_details.get('time', ''),
                'fees': order_details.get('fees', ''),
                'currency': currency_asset,
            }
        else:
            return {
                'message': f"Trade opened with order ID {response.get('orderId')}.",
                'order_id': response.get('orderId'),
                'closed_order_id': response.get('orderId'),
                'symbol': response.get('symbol', symbol),
                "side": side.upper(),
                'price': 0,
                # 'fees': response['fills'][0]['commission'],
                'qty': adjusted_quantity,
                'currency': currency_asset,
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


def get_order_details(account, symbol, order_id):
    try:
        order_endpoint = '/api/v2/spot/trade/fills'

        if account.type == "U":
            productType = "USDT-FUTURES"
            order_endpoint = '/api/v2/mix/order/fills'

        elif account.type == "C":
            productType = "COIN-FUTURES"
            order_endpoint = '/api/v2/mix/order/fills'

        elif account.type == "UC":
            productType = "USDC-FUTURES"
            order_endpoint = '/api/v2/mix/order/fills'
        

        order_url = order_endpoint + f"?orderId={order_id}"

        if account.type != 'S':
            order_url += f"&productType={productType}&symbol={symbol}"

        response = send_request('GET', order_url, account.apiKey, account.secretKey, account.pass_phrase)
        response = response.get('data')

        if account.type != 'S':
            response = response.get('fillList')

        # print("trade data => ", response) 
        
        if response is None:
            raise ValueError("No data found in response")
        

        if isinstance(response, list):
            if len(response) > 1:
                total_qty = sum(float(t.get('size', 0)) for t in response)
                # Use the last fill as the base record
                trade = response[-1]
                trade['size'] = str(total_qty)
                
                # Sum total_commission across all fills, handling list or dict in feeDetail
                total_commission = 0.0
                for t in response:
                    fd = t.get('feeDetail', {})
                    if isinstance(fd, list):
                        for entry in fd:
                            total_commission += float(entry.get('totalFee', 0))
                    elif isinstance(fd, dict):
                        total_commission += float(fd.get('totalFee', 0))
                fee_detail = trade.get('feeDetail')
                if not isinstance(fee_detail, dict):
                    fee_detail = {}
                fee_detail['totalFee'] = str(total_commission)
                trade['feeDetail'] = fee_detail
            else:
                trade = response[0]
        else:
            trade = response
        

        if trade:

            sym_info = get_exchange_info(account, symbol)
            # Fallback to 'price' if 'priceAvg' is missing or falsy
            price_str = trade.get('priceAvg') or trade.get('price', '0')
            price_usdt = Decimal(str(price_str))

            # Normalize fee detail, which may be a dict or a list of dicts
            fee_detail = trade.get('feeDetail', {})
            total_fees = Decimal('0')

            if isinstance(fee_detail, list):
                # Sum and convert each fee entry
                for fd in fee_detail:
                    amt = Decimal(str(fd.get('totalFee', '0')))
                    coin = fd.get('feeCoin')
                    if coin == sym_info.get('baseCoin'):
                        total_fees += amt * price_usdt
                    else:
                        total_fees += amt
            else:
                amt = Decimal(str(fee_detail.get('totalFee', '0')))
                coin = fee_detail.get('feeCoin')
                if coin == sym_info.get('baseCoin'):
                    total_fees = amt * price_usdt
                else:
                    total_fees = amt

            # Use the computed total_fees
            fees = total_fees

            ts_s = float(trade.get('cTime')) / 1000  # e.g. 1683474419
            dt_naive = datetime.fromtimestamp(ts_s)
            dt_aware = timezone.make_aware(dt_naive, timezone=timezone.utc)
            
            r = {
                'order_id': str(trade.get('orderId')),
                'symbol': str(trade.get('symbol')),
                'volume': str(trade.get('size') or trade.get('baseVolume')),
                'side': str(trade.get('side')),
                
                'time': dt_aware,
                'price': str(price_str),

                'profit': str(trade.get('profit', None)),

                'fees': str(abs(fees)),

                'feeDetail': str(trade.get('feeDetail')),
            }

            return r 
        
        return None

    except Exception as e:
        print('error getting order details: ', str(e))
        return None
    

def get_bitget_order_details(account, trade):

    trade_id = trade.closed_order_id

    try:
        result = get_order_details(account, trade.symbol, trade_id)

        if result:
            # Convert price and volume to Decimal for accurate calculation
            try:
                price_dec = Decimal(str(result.get('price', '0')))
            except Exception as e:
                price_dec = Decimal('0')
            try:
                volume_dec = Decimal(str(result.get('volume', '0')))
            except Exception as e:
                volume_dec = Decimal('0')

            if result.get('profit') in (None, '', 'None'):
                if price_dec != 0:
                    side_upper = trade.side.upper()
                    if side_upper in ("B", "BUY"):
                        profit = (price_dec - Decimal(str(trade.entry_price))) * volume_dec
                    elif side_upper in ("S", "SELL"):
                        profit = (Decimal(str(trade.entry_price)) - price_dec) * volume_dec
                    else:
                        profit = Decimal("0")
                else:
                    profit = Decimal("0")
            else:
                profit = result.get('profit')

            res = {
                'order_id': str(result.get('order_id')),
                'symbol': str(result.get('symbol')),
                'volume': str(result.get('volume')),
                'side': str(result.get('side')),

                'open_price': str(trade.entry_price),
                'close_price': str(result.get('price')),

                'open_time': str(trade.entry_time),
                'close_time': str(result.get('time')), 

                'fees': str(result.get('fees')), 
                'profit': str(profit),

                'feeDetail': str(result.get('feeDetail')),
            }

            return res
        
        return None

    except Exception as e:
        print("Error:", e)
        return None