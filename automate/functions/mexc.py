import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode


BASE_URL = "https://api.mexc.com"


def _get_timestamp():
    return int(time.time() * 1000)


def create_signature(query_string, secret):
    return hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()


def get_account_info(api_key, secret):
    endpoint = "/api/v3/account"
    params = {
        "timestamp": _get_timestamp()
    }
    query_string = urlencode(params)
    signature = create_signature(query_string, secret)
    params["signature"] = signature
    headers = {
        "X-MEXC-APIKEY": api_key
    }
    response = requests.get(BASE_URL + endpoint, params=params, headers=headers)
    return response.json()


def new_order(api_key, secret, order_params):
    endpoint = "/api/v3/order"
    order_params["timestamp"] = _get_timestamp()
    query_string = urlencode(order_params)
    signature = create_signature(query_string, secret)
    order_params["signature"] = signature
    headers = {
        "X-MEXC-APIKEY": api_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(BASE_URL + endpoint, data=order_params, headers=headers)
    return response.json()


def check_mexc_credentials(api_key, api_secret, trade_type="spot"):
    try:
        account_info = get_account_info(api_key, api_secret)
        # Assuming a successful response returns a code of 200
        if account_info.get("code") != 200:
            return {"error": account_info.get("message", "Invalid credentials"), "valid": False}
        return {"message": "API credentials are valid.", "valid": True}
    except Exception as e:
        return {"error": str(e)}


def get_account_balance(mexc_account, asset: str):
    try:
        account_info = get_account_info(mexc_account.apiKey, mexc_account.secretKey)
        if account_info.get("code") != 200:
            raise ValueError(account_info.get("message", "Failed to retrieve account info"))
        balances = {}
        # Expected structure:
        # {"code":200, "data": {"balances": [{"asset": "BTC", "free": "0.1", ...}, ...]}}
        for balance in account_info["data"]["balances"]:
            balances[balance["asset"]] = float(balance["free"])
        return {"asset": asset, "balance": balances.get(asset, 0.0)}
    except Exception as e:
        raise ValueError(str(e))


def adjust_trade_quantity(mexc_account, symbol, side, quote_order_qty):
    try:
        # Assuming symbol format like 'BTCUSDT' where the last 4 characters denote the quote asset.
        base_asset, quote_asset = symbol[:-4], symbol[-4:]
        base_balance = get_account_balance(mexc_account, base_asset)["balance"]
        quote_balance = get_account_balance(mexc_account, quote_asset)["balance"]

        print("Base asset:", base_asset)
        print("Quote asset:", quote_asset)
        print("Base balance:", base_balance)
        print("Quote balance:", quote_balance)

        if side.upper() == "BUY":
            if quote_balance < quote_order_qty:
                return quote_balance
            elif quote_balance <= 0:
                raise ValueError("Insufficient quote balance.")
        elif side.upper() == "SELL":
            if base_balance < quote_order_qty:
                return base_balance
            elif base_balance <= 0:
                raise ValueError("Insufficient base balance.")
        return quote_order_qty
    except Exception as e:
        raise ValueError(str(e))


def open_mexc_trade(mexc_account, symbol: str, side: str, quantity: float, custom_id: str = None):
    try:
        adjusted_quantity = adjust_trade_quantity(mexc_account, symbol, side, float(quantity))
        print("Adjusted quantity:", adjusted_quantity)

        
        if mexc_account.type == "F":
            return open_mexc_futures_trade(mexc_account, symbol, side, adjusted_quantity, custom_id)

        order_params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "market",  # Using lowercase as per MEXC docs
            "quantity": adjusted_quantity,
        }
        response = new_order(mexc_account.apiKey, mexc_account.secretKey, order_params)
        
        if response.get("code") != 200:
            raise ValueError(response.get("message", "Order placement failed"))
        order_data = response["data"]
        
        return {
            "order_id": order_data["order_id"],
            "symbol": symbol,
            "side": side.upper(),
            "price": order_data["price"] if "price" in order_data else "0",  # Market orders typically don't have a set price
            "qty": adjusted_quantity,
        }
    except Exception as e:
        raise ValueError(str(e))


def close_mexc_trade(mexc_account, symbol: str, side: str, quantity: float):
    try:
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        adjusted_quantity = adjust_trade_quantity(mexc_account, symbol, t_side, float(quantity))

        if mexc_account.type == "F":
            return close_mexc_futures_trade(mexc_account, symbol, side, adjusted_quantity)

        order_params = {
            "symbol": symbol,
            "side": t_side.upper(),
            "type": "market",
            "quantity": adjusted_quantity,
        }
        response = new_order(mexc_account.apiKey, mexc_account.secretKey, order_params)
        if response.get("code") != 200:
            raise ValueError(response.get("message", "Order placement failed"))
        order_data = response["data"]
        
        return {
            "order_id": order_data["order_id"],
            "symbol": symbol,
            "side": t_side.upper(),
            "price": order_data["price"] if "price" in order_data else "0", 
            "qty": adjusted_quantity,
        }
    except Exception as e:
        raise ValueError(str(e))



FUTURES_BASE_URL = "https://contract.mexc.com"

def get_futures_account_info(api_key, secret):
    """Retrieve futures account information using MEXC futures API."""
    endpoint = "/api/v1/private/account"
    params = {"timestamp": _get_timestamp()}
    query_string = urlencode(params)
    signature = create_signature(query_string, secret)
    params["signature"] = signature
    headers = {"X-MEXC-APIKEY": api_key}
    response = requests.get(FUTURES_BASE_URL + endpoint, params=params, headers=headers)
    return response.json()


def new_futures_order(api_key, secret, order_params):
    """Place a new futures order using MEXC futures API."""
    endpoint = "/api/v1/private/order"
    order_params["timestamp"] = _get_timestamp()
    query_string = urlencode(order_params)
    signature = create_signature(query_string, secret)
    order_params["signature"] = signature
    headers = {
        "X-MEXC-APIKEY": api_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(FUTURES_BASE_URL + endpoint, data=order_params, headers=headers)
    return response.json()


def open_mexc_futures_trade(mexc_account, symbol: str, side: str, quantity: float, custom_id: str = None):
    """Open a new futures trade on MEXC. Note: futures orders may require additional parameters such as leverage and margin type."""
    try:
        order_params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "market",
            "quantity": quantity,
        }
        response = new_futures_order(mexc_account.apiKey, mexc_account.secretKey, order_params)
        if response.get("code") != 200:
            raise ValueError(response.get("message", "Futures order placement failed"))
        order_data = response["data"]
        return {
            "order_id": order_data.get("order_id"),
            "symbol": symbol,
            "side": side.upper(),
            "price": order_data.get("price", "0"),
            "qty": quantity,
        }
    except Exception as e:
        raise ValueError(str(e))


def close_mexc_futures_trade(mexc_account, symbol: str, side: str, quantity: float):
    """Close an existing futures trade on MEXC by placing an opposite order."""
    try:
        # Reverse the side for closing the position
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        order_params = {
            "symbol": symbol,
            "side": t_side.upper(),
            "type": "market",
            "quantity": quantity,
        }
        response = new_futures_order(mexc_account.apiKey, mexc_account.secretKey, order_params)
        if response.get("code") != 200:
            raise ValueError(response.get("message", "Futures order placement failed"))
        order_data = response["data"]
        return {
            "order_id": order_data.get("order_id"),
            "symbol": symbol,
            "side": t_side.upper(),
            "price": order_data.get("price", "0"),
            "qty": quantity,
        }
    except Exception as e:
        raise ValueError(str(e))