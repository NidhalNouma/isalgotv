import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.utils import timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP


BASE_URL = "https://api.crypto.com/exchange/v1/"


def _get_timestamp():
    return int(time.time() * 1000)

def create_signature(req, secret):
    MAX_LEVEL = 3

    def params_to_str(obj, level):
        if level >= MAX_LEVEL:
            return str(obj)
        return_str = ""
        for key in sorted(obj):
            return_str += key
            if obj[key] is None:
                return_str += 'null'
            elif isinstance(obj[key], list):
                for subObj in obj[key]:
                    return_str += params_to_str(subObj, level + 1)
            else:
                return_str += str(obj[key])
        return return_str

    param_str = ""
    if "params" in req:
        param_str = params_to_str(req["params"], 0)
    payload_str = req["method"] + str(req["id"]) + req["api_key"] + param_str + str(req["nonce"])
    return hmac.new(secret.encode('utf-8'), payload_str.encode('utf-8'), hashlib.sha256).hexdigest()

def get_account_info(api_key, secret):
    """Retrieve account information from Crypto.com Exchange API using JSON-RPC."""

    nonce = _get_timestamp()
    payload = {
        "id": nonce,
        "method": "private/user-balance",
        "api_key": api_key,
        "params": {},
        "nonce": nonce
    }
    payload['sig'] = create_signature(payload, secret)

    headers = {"Content-Type": "application/json"}
    response = requests.post(BASE_URL + payload["method"], json=payload, headers=headers)
    return response.json()

def get_exchange_info(symbol):
    """Retrieve exchange information for a specific symbol from Crypto.com Exchange API."""
    url = BASE_URL + f'public/get-instruments?instrument_name={symbol}'
    response = requests.get(url)

    res_json = response.json()    
    data_list = res_json.get('result', {}).get('data', [])
    
    target = symbol.upper()
    for item in data_list:
        inst = item.get('symbol', '')
        if inst.replace('_', '').upper() == target or inst == target:
            return item
    return None


def new_order(api_key, secret, order_params):
    """Place a new order via the Crypto.com Exchange API using JSON-RPC."""
    nonce = _get_timestamp()
    payload = {
        "id": nonce,
        "method": "private/create-order",
        "api_key": api_key,
        "params": order_params,
        "nonce": nonce
    }

    payload["sig"] = create_signature(payload, secret)
    headers = {"Content-Type": "application/json"}

    response = requests.post(BASE_URL + payload["method"], json=payload, headers=headers)
    
    return response.json()


def check_crypto_credentials(api_key, secret, trade_type="spot"):
    """Verify Crypto.com API credentials."""
    try:
        account_info = get_account_info(api_key, secret)
        print("Account Info:", account_info)  # Debugging line to check the response
        if account_info.get("code") != 0:
            return {"error": account_info.get("message", "Invalid credentials"), "valid": False}
        return {"message": "API credentials are valid.", "valid": True}
    except Exception as e:
        return {"error": str(e)}


def get_account_balance(crypto_account, asset: str):
    """Retrieve the balance for a specific asset from Crypto.com account info."""
    try:
        account_info = get_account_info(crypto_account.apiKey, crypto_account.secretKey)

        if account_info.get("code") != 0:
            raise ValueError(account_info.get("message", "Failed to retrieve account info"))
        balances = {}
        
        data = account_info["result"]["data"][0]
        # print("Balances Data:", data["position_balances"]) 
        
        for balance in data["position_balances"]:  # Debugging line to check each balance
            balances[balance["instrument_name"]] = float(balance["quantity"])
            
        return {"asset": asset, "balance": balances.get(asset, 0.0)}

    except Exception as e:
        raise ValueError(str(e))

    


def adjust_trade_quantity(crypto_account, symbol_info, side, quote_order_qty):
    """Adjust the trade quantity based on available balances. Assumes symbol format like 'BTCUSDT'."""
    try:
        
        base_asset = symbol_info.get('base_ccy')
        quote_asset = symbol_info.get('quote_ccy')

        base_decimals = symbol_info.get('quantity_decimals')
        quote_decimals = symbol_info.get('quote_decimals')

        base_balance = get_account_balance(crypto_account, base_asset)["balance"]
        quote_balance = get_account_balance(crypto_account, quote_asset)["balance"]

        print("Base asset:", base_asset)
        print("Quote asset:", quote_asset)
        print("Base balance:", base_balance)
        print("Quote balance:", quote_balance)

        # Determine precision for quantity formatting
        try:
            precision = int(base_decimals)
        except (TypeError, ValueError):
            precision = 8  # fallback precision
        quant = Decimal(1).scaleb(-precision)  # smallest step based on precision

        if side.upper() == "BUY":
            if float(quote_balance) <= 0:
                raise ValueError("Insufficient quote balance.")
            # elif quote_balance < quote_order_qty:
            #     return quote_balance
            # Format quantity to max base_decimals and return as string
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
    except Exception as e:
        raise ValueError(str(e))


def open_crypto_trade(crypto_account, symbol: str, side: str, quantity: float, custom_id: str = ''):
    """Open a new crypto trade via the Crypto.com API."""
    try:

        symbol_info = get_exchange_info(symbol)
        if not symbol_info:
            raise Exception('Symbol was not found!')

        adjusted_quantity = adjust_trade_quantity(crypto_account, symbol_info, side, float(quantity))

        if float(adjusted_quantity) <= 0:
            raise ValueError("Insufficient quote balance.")

        print("Adjusted quantity:", adjusted_quantity)

        quote_asset = symbol_info.get('quote_ccy')
        order_symbol = symbol_info.get('symbol')

        order_params = {
            "instrument_name": order_symbol,
            "side": side.upper(),
            "type": "MARKET", 
            "quantity": str(adjusted_quantity),
        }
        if custom_id:
            order_params["client_oid"] = custom_id
        # print(order_params)

        response = new_order(crypto_account.apiKey, crypto_account.secretKey, order_params)
        if response.get("code") != 0:
            raise ValueError(response.get("message", "Order placement failed"))
        
        # print("Order Response:", response)  # Debugging line to check the response
        order_data = response["result"]
        
        order_id = order_data["order_id"]
        order_details = get_order_details(crypto_account, order_id)

        if order_details:
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': order_id,
                'symbol': symbol,
                "side": side.upper(),
                'qty': adjusted_quantity,
                'price': order_details.get('price', '0'),
                'time': order_details.get('time', ''),
                'fees': order_details.get('fees', ''),
                'currency': quote_asset,
            }
        else:
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': order_id,
                'symbol': symbol,
                "side": side.upper(),
                'qty': adjusted_quantity,
                'price': order_data.get('price', '0'),
                'time': timezone.now(),
                'currency': quote_asset,
            }
    
    except Exception as e:
        raise ValueError(str(e))


def close_crypto_trade(crypto_account, symbol: str, side: str, quantity: float):
    """Close an existing crypto trade by placing an opposite order via the Crypto.com API."""
    try:
        # Reverse the side for closing the position
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        
        symbol_info = get_exchange_info(symbol)
        if not symbol_info:
            raise Exception('Symbol was not found!')

        adjusted_quantity = adjust_trade_quantity(crypto_account, symbol_info, t_side, float(quantity))

        if float(adjusted_quantity) <= 0:
            raise ValueError("Insufficient quote balance.")
        
        order_symbol = symbol_info.get('symbol')

        
        order_params = {
            "instrument_name": order_symbol,
            "side": t_side.upper(),
            "type": "MARKET",  
            "quantity": str(adjusted_quantity),
        }

        response = new_order(crypto_account.apiKey, crypto_account.secretKey, order_params)
        if response.get("code") != 0:
            raise ValueError(response.get("message", "Order placement failed"))
        
        order_data = response["result"]
        return {
            "closed_order_id": order_data["order_id"],
            "symbol": symbol,
            "side": t_side.upper(),
            "price": order_data.get("price", "0"),
            "qty": adjusted_quantity,
        }
    except Exception as e:
        raise ValueError(str(e))
    
def get_order_details(account, trade_id):
    try:

        nonce = _get_timestamp()
        payload = {
            "id": nonce,
            "method": "private/get-order-detail",
            "api_key": account.apiKey,
            "params": {
                "order_id": trade_id
            },
            "nonce": nonce
        }
        payload['sig'] = create_signature(payload, account.secretKey)

        headers = {"Content-Type": "application/json"}
        response = requests.post(BASE_URL + payload["method"], json=payload, headers=headers)
        data = response.json()

        if data.get("code") == 0:
            result = data.get("result", {})
            
            # print(result)
            if result:
                sym_info = get_exchange_info(str(result.get('instrument_name')))

                ts_s = result.get('create_time') / 1000  # e.g. 1683474419
                dt_naive = datetime.fromtimestamp(ts_s)
                dt_aware = timezone.make_aware(dt_naive, timezone=timezone.utc)

                fees = float(result.get('cumulative_fee'))
                # Convert fees from ADA to USDT using avg_price

                if str(result.get('fee_instrument_name')) == sym_info.get('base_ccy'):
                    # print('changing fees ..')
                    try:
                        fee_ada = Decimal(str(fees))
                        price_usdt = Decimal(str(result.get('avg_price', '0')))
                        fees = fee_ada * price_usdt
                    except (InvalidOperation, ValueError):
                        pass

                r = {
                    'order_id': str(result.get('order_id')),
                    'symbol': str(result.get('instrument_name')),
                    'volume': str(result.get('quantity')),
                    'side': str(result.get('side')),
                    'order_value': str(result.get('order_value')),
                    'time': dt_aware,
                    'price': str(result.get('avg_price')),

                    'fees': str(fees),
                    'maker_fee_rate': str(result.get('maker_fee_rate')),
                    'taker_fee_rate': str(result.get('taker_fee_rate')),
                    'fees_currency': str(result.get('fee_instrument_name')),
                }
                return r
        
        return None
        
    except Exception as e:
        print('Error get crypto order details, ', e)
        return None



def get_crypto_order_details(account, trade):

    trade_id = trade.closed_order_id

    try:
        result = get_order_details(account, trade_id)

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
                'fees_currency': str(result.get('fees_currency')), 

                'profit': str(profit),
            }

            return res
        
        return None

    except Exception as e:
        print("Error:", e)
        return None

    
