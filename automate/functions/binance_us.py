import time
import hmac
import hashlib
import requests
from django.utils import timezone
from datetime import datetime

from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP


API_URL = 'https://api.binance.us'


def create_signature(query_string, secret):
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()


def send_request(method, endpoint, api_key, api_secret, params={}, with_signuture = True):
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    timestamp = int(time.time() * 1000)
    
    headers = {
        'X-MBX-APIKEY': api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    if with_signuture:
        query_string += f"&timestamp={timestamp}"
        signature = create_signature(query_string, api_secret)
        query_string += f"&signature={signature}"

    url = f"{API_URL}{endpoint}?{query_string}"
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


def get_exchange_info(api_key, api_secret, symbol):
    params = {
        "symbol": symbol,
    }
    response = send_request('GET', '/api/v3/exchangeInfo', api_key, api_secret, params, False)
            
    if isinstance(response, list):
        data_list = response
    else:
        data_list = response.get('symbols', [])
    
    target = symbol.upper()
    for item in data_list:
        inst = item.get('symbol', '')
        if inst.replace('_', '').upper() == target or inst == target:
            return item
    return None

def get_account_balance(account, asset):
    """Fetch the available balance for a specific asset."""
    response = send_request('GET', '/api/v3/account', account.apiKey, account.secretKey)
    balances = {item['asset']: float(item['free']) for item in response['balances']}
    return balances.get(asset, 0)

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
    
def adjust_trade_quantity(account, symbol_info, quote_order_qty, trade_type):
    """Adjust the trade quantity based on available balance."""
    try:
        base_asset = symbol_info.get('baseAsset')
        quote_asset = symbol_info.get('quoteAsset')

        # find the filters
        price_filter = next(f for f in symbol_info['filters'] if f['filterType']=='PRICE_FILTER')
        lot_filter   = next(f for f in symbol_info['filters'] if f['filterType']=='LOT_SIZE')

        quote_decimals = get_decimals_from_step(price_filter['tickSize'])
        base_decimals   = get_decimals_from_step(lot_filter['stepSize'])

        base_balance = get_account_balance(account, base_asset)
        quote_balance = get_account_balance(account, quote_asset)

        # print(symbol_info)
        # print(base_decimals, price_filter, quote_decimals)

        try:
            precision = int(base_decimals)
        except (TypeError, ValueError):
            precision = 8  # fallback precision
        quant = Decimal(1).scaleb(-precision)  
        
        if trade_type.upper() == "BUY":

            if float(quote_balance) <= 0:
                raise ValueError("Insufficient quote balance.")
            # elif quote_balance < quote_order_qty:
            #     return quote_balance
            # Format quantity to max base_decimals and return as string
            qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
            return format(qty_dec, f'.{precision}f')
        
        elif trade_type.upper() == "SELL":
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
    except Exception as e:
        print('adjust trade quantity error: ', str(e))
        return quote_order_qty


def open_binance_us_trade(account, symbol, side, quantity, custom_id):
    try:

        symbol_info = get_exchange_info(account.apiKey, account.secretKey, symbol)

        if not symbol_info:
            raise Exception('Symbol was not found!')

        adjusted_quantity = adjust_trade_quantity(account, symbol_info, float(quantity), side)

        quote_asset = symbol_info.get('quoteAsset')
        order_symbol = symbol_info.get('symbol')

        params = {
            "symbol": order_symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": adjusted_quantity,
            # "quoteOrderQty": adjusted_quantity
        }

        print("Quantity:", quantity, "Qty:", adjusted_quantity)

        response = send_request('POST', '/api/v3/order', account.apiKey, account.secretKey, params)
        
        if response.get('msg') is not None:
            raise Exception(response.get('msg'))
        
        
        order_id = response.get("orderId")
        order_details = get_order_info(account, symbol, order_id)

        if order_details:
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': order_id,
                'symbol': symbol,
                "side": side.upper(),
                'qty': order_details.get('volume', adjusted_quantity),
                'price': order_details.get('price', '0'),
                'time': order_details.get('time', ''),
                'fees': order_details.get('fees', ''),
                'currency': quote_asset,
            }
        else:
            return {
            'message': f"Trade opened with order ID {response.get('orderId')}.",
            'order_id': response.get('orderId'),
            'symbol': response.get('symbol', symbol),

            'price': response['fills'][0]['price'],
            # 'fees': response['fills'][0]['commission'],
            'qty': response.get('executedQty', adjusted_quantity),
            'currency': quote_asset,
            }

    except Exception as e:
        return {'error': str(e)}


def close_binance_us_trade(account, symbol, side, quantity):
    t_side = "SELL" if side.upper() == "BUY" else "BUY"
    try:
        
        symbol_info = get_exchange_info(account.apiKey, account.secretKey, symbol)

        if not symbol_info:
            raise Exception('Symbol was not found!')

        adjusted_quantity = adjust_trade_quantity(account, symbol_info, float(quantity), side)

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
            "symbol": symbol,

            "id": response.get('orderId'),
            "closed_order_id": response["orderId"],
            "side": t_side.upper(),
            'price': response['fills'][0]['price'],
            'qty': response.get('executedQty', adjusted_quantity),
        }
    except Exception as e:        
        return {'error': str(e)}


def get_asset_price(symbol):
    url = API_URL + "/api/v3/ticker/price"
    response = requests.get(url, params={"symbol": symbol})
    response.raise_for_status()
    price_data = response.json()
    return float(price_data["price"])

def get_order_info(account, symbol, order_id):
    try:

        params = {
            "symbol": symbol,
            "orderId": order_id,
        }

        response = send_request('GET', '/api/v3/myTrades', account.apiKey, account.secretKey, params)

        if isinstance(response, dict) and response.get('msg') is not None:
            raise Exception(response.get('msg'))
        
        if isinstance(response, list):
            if not response:
                return None
            if len(response) > 1:
                total_qty = sum(float(t.get('qty', 0)) for t in response)
                total_commission = sum(float(t.get('commission', 0)) for t in response)
                # Use the last fill as the base record
                trade = response[-1]
                trade['qty'] = str(total_qty)
                trade['commission'] = str(total_commission)
            else:
                trade = response[0]
        else:
            trade = response

        sym_info = get_exchange_info(account.apiKey, account.secretKey, symbol)

        fees = float(trade.get('commission'))
        # Convert fees from ADA to USDT using avg_price

        if str(trade.get('commissionAsset')) == sym_info.get('baseAsset'):
            try:
                fee_ada = Decimal(str(fees))
                price_usdt = Decimal(str(trade.get('price', '0')))
                fees = fee_ada * price_usdt
            except (InvalidOperation, ValueError):
                pass
        
        

        ts_s = trade.get('time') / 1000  # e.g. 1683474419
        dt_naive = datetime.fromtimestamp(ts_s)
        dt_aware = timezone.make_aware(dt_naive, timezone=timezone.utc)

        
        r = {
            'order_id': str(trade.get('orderId')),
            'symbol': str(trade.get('symbol')),
            'volume': str(trade.get('qty')),
            'side': str(trade.get('side')),
            
            'time': dt_aware,
            'price': str(trade.get('price')),

            'fees': str(fees),

            'commission': str(trade.get('commission')),
            'commissionAsset': str(trade.get('commissionAsset')),
        }

        return r
    except Exception as e:     
        print('getting trade info ', e)   
        return None


def get_binanceus_order_details(account, trade):

    trade_id = trade.closed_order_id

    try:
        result = get_order_info(account, trade.symbol, trade_id)

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


            side_upper = trade.side.upper()
            if side_upper in ("B", "BUY"):
                profit = (price_dec - Decimal(str(trade.entry_price))) * volume_dec
            elif side_upper in ("S", "SELL"):
                profit = (Decimal(str(trade.entry_price)) - price_dec) * volume_dec
            else:
                profit = Decimal("0")

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

                'commission': str(result.get('commission')),
                'commissionAsset': str(result.get('commissionAsset')),
            }

            return res
        
        return None

    except Exception as e:
        print("Error:", e)
        return None