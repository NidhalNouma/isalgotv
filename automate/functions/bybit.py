import time
import hmac
import hashlib
import requests
import json

from django.utils import timezone
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP

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
    

def get_decimals_from_step(size_str):
    """
    Determine the number of decimal places allowed by a step size,
    stripping any trailing zeros in the step definition.
    """
    d = Decimal(size_str)
    # Normalize to remove any trailing zeros (e.g., '0.10000000' -> '0.1')
    d_norm = d.normalize()
    exp = d_norm.as_tuple().exponent
    return max(-exp, 0)
    
def get_exchange_info(account, symbol):
    try:
        if account.type == "S":
            category = 'spot'
        else:
            category = 'linear'

        params = {
            'symbol': symbol,
            'category': category,
        }
        response = send_bybit_request('GET', '/market/instruments-info', account.apiKey, account.secretKey, params)

        data = response['result']['list'][0]

        if category == 'linear':
            precison = data['lotSizeFilter']['qtyStep']

            quote_decimals = get_decimals_from_step(precison)
            base_decimals   = get_decimals_from_step(precison)
        else:
            b_precison = data['lotSizeFilter']['basePrecision']
            q_precison = data['lotSizeFilter']['quotePrecision']

            quote_decimals = get_decimals_from_step(q_precison)
            base_decimals   = get_decimals_from_step(b_precison)

        r ={
            'symbol': data['symbol'],
            'baseCoin': data['baseCoin'],
            'quoteCoin': data['quoteCoin'],
            'baseDecimals': base_decimals,
            'quoteDecimals': quote_decimals
        }
        print(r)

        return r

    except Exception as e:
        raise Exception(e)
    

def get_account_balance(account):
    """Get the balance of a specific asset on Bybit."""
    try:
        params = {
            'accountType': 'UNIFIED',
            # 'coin': coin
        }
        endpoint = '/account/wallet-balance'
        response = send_bybit_request('GET', endpoint, account.apiKey, account.secretKey, params)
        # print('coin', response)
        if response['retCode'] != 0:
            raise Exception(response['retMsg'])
        
        b = {}
        for balance in response['result']['list'][0]['coin']:
            # if balance['coin'] == coin:
            b[balance['coin']] = balance['walletBalance']
        return b
    except Exception as e:
        raise Exception(e)
    
def adjust_trade_quantity(account, symbol_info, side, quote_order_qty):
    try:
        base_asset = symbol_info.get('baseCoin')
        quote_asset = symbol_info.get('quoteCoin')

        account_balace = get_account_balance(account)
        print("Account balance:", account_balace)

        base_balance = account_balace.get(base_asset, 0)
        quote_balance = account_balace.get(quote_asset, 0)

        base_decimals = symbol_info.get('baseDecimals') 
        quote_decimals = symbol_info.get('quoteDecimals') 

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

                qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
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

    

def open_bybit_trade(account, symbol, side, quantity):
    """Place a market order on Bybit."""
    try:
        if account.type == "S":
            category = 'spot'
        else:
            category = 'linear'
            
        sys_info = get_exchange_info(account, symbol)

        if not sys_info:
            raise Exception('Symbol was not found!')
        
        currency_asset = sys_info.get('quoteCoin')
        base_asset = sys_info.get('baseCoin')
        order_symbol = sys_info.get('symbol')

        adjusted_quantity =  adjust_trade_quantity(account, sys_info, side, float(quantity))
        print("Adjusted quantity:", adjusted_quantity)

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

        raise ValueError("Invalid quantity")
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
            # 'price': price,
            'qty': qty
        }
    except Exception as e:
        return {'error': str(e)}

def close_bybit_trade(account, symbol, side, quantity):
    """Close a trade on Bybit."""
    opposite_side = 'Sell' if side == 'Buy' else 'Buy'
    return open_bybit_trade(account, symbol, opposite_side, quantity)


def get_order_details(account, symbol, order_id):
    try:
        order_endpoint = '/v5/execution/list'

        if account.type == "S":
            category = 'spot'
        else:
            category = 'linear'

        params = {
            'symbol': symbol,
            'orderId': order_id,
            
            'category': category,
        }


        response = send_bybit_request('GET', order_endpoint, account.apiKey, account.secretKey, params)

        response = response.get('result', {}).get('list', [])

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

def get_bybit_order_details():
    pass
