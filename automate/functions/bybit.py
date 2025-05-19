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
        # print('get_exchange_info', symbol, response, params)

        if response['retCode'] != 0:
            raise Exception(response['retMsg'])

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

    

def open_bybit_trade(account, symbol, side, quantity, additional_params={}):
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
        if float(adjusted_quantity) <= 0:
            raise ValueError("Insufficient balance for the trade.")

        endpoint = '/order/create'
        params = {
            'symbol': order_symbol,
            'side': side.capitalize(),
            'order_type': 'Market',
            'qty': str(adjusted_quantity),
            
            'category': category,

            'marketUnit': 'baseCoin',
            'time_in_force': 'IOC',
            **additional_params
        }
            
        response = send_bybit_request('POST', endpoint, account.apiKey, account.secretKey, params)

        # print(response)
        if response['retCode'] != 0:
            raise Exception(response['retMsg'])
        
        order_id = response['result']['orderId']

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

                # 'trade_details': order_details
            }
        
        else:
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': order_id,
                'closed_order_id': order_id,
                'symbol': symbol,
                "side": side.upper(),
                'qty': adjusted_quantity,
                'currency': currency_asset,
            }
    except Exception as e:
        return {'error': str(e)}

def close_bybit_trade(account, symbol, side, quantity):
    """Close a trade on Bybit."""
    opposite_side = "sell" if side.lower() == "buy" else "buy"

    additional_params = {
        'reduceOnly': 'true',
        'closeOnTrigger': 'true',
    }
    return open_bybit_trade(account, symbol, opposite_side, quantity, additional_params)


def get_order_details(account, symbol, order_id):
    try:
        endpoint = '/execution/list'

        if account.type == "S":
            category = 'spot'
        else:
            category = 'linear'

        params = {
            'category': category,
            'symbol': symbol,
            'orderId': order_id,
        }

        response = send_bybit_request('GET', endpoint, account.apiKey, account.secretKey, params)
        response = response.get('result', {}).get('list', [])
        
        if response is None:
            raise ValueError("No data found in response")
        
        if isinstance(response, list):
            if len(response) > 1:
                total_qty = sum(float(t.get('execQty', 0)) for t in response)
                total_commission = sum(float(t.get('execFee', 0)) for t in response)
                
                trade = response[-1]
                trade['execFee'] = str(total_commission)
                trade['execQty'] = str(total_qty)

            else:
                trade = response[0]
        else:
            trade = response

        if trade:

            sym_info = get_exchange_info(account, symbol)
            # Fallback to 'price' if 'priceAvg' is missing or falsy
            price_str = trade.get('execPrice') or trade.get('orderPrice', '0')
            price_usdt = Decimal(str(price_str))

            # Normalize fee detail, which may be a dict or a list of dicts
            fees = trade.get('execFee', 0)
            sym_info = get_exchange_info(account, symbol)

            try:
                fees = Decimal(str(fees))
                if str(trade.get('feeCurrency')) == sym_info.get('baseCoin'):
                    fees = fees * price_usdt
            except (InvalidOperation, ValueError):
                pass


            ts_s = float(trade.get('execTime')) / 1000  # e.g. 1683474419
            dt_naive = datetime.fromtimestamp(ts_s)
            dt_aware = timezone.make_aware(dt_naive, timezone=timezone.utc)
            
            r = {
                'order_id': str(trade.get('orderId')),
                'symbol': str(trade.get('symbol')),
                'volume': str(trade.get('execQty') or trade.get('orderQty')),
                'side': str(trade.get('side')),
                
                'time': dt_aware,
                'price': str(price_str),

                'profit': str(trade.get('profit', None)),

                'fees': str(abs(fees)),

                'execFee': str(trade.get('execFee')),
                'feeCurrency': str(trade.get('feeCurrency')),
                'feeRate': str(trade.get('feeRate')),
            }

            return r 
        
        return None

    except Exception as e:
        print('error getting order details: ', str(e))
        return None

def get_bybit_order_details(account, trade):
    trade_id = trade.closed_order_id or trade.order_id

    try:
        result = get_order_details(account, trade.symbol, trade_id)

        if result:
            # Convert price and volume to Decimal for accurate calculation
            try:
                price_dec = Decimal(str(result.get('price', '0')))
            except (InvalidOperation, ValueError):
                price_dec = Decimal('0')
            try:
                volume_dec = Decimal(str(result.get('volume', '0')))
            except (InvalidOperation, ValueError):
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

                'execFee': str(result.get('execFee')),
                'feeCurrency': str(result.get('feeCurrency')),
                'feeRate': str(result.get('feeRate')),
            }

            return res
        
        return None

    except Exception as e:
        print("Error:", e)
        return None
