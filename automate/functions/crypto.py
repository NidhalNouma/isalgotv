import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode


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
        # Expected structure: {"code":200, "data": {"balances": [{"asset": "BTC", "free": "0.1", ...}, ...]}}
        for balance in account_info["data"]["balances"]:
            balances[balance["asset"]] = float(balance["free"])
        return {"asset": asset, "balance": balances.get(asset, 0.0)}
    except Exception as e:
        raise ValueError(str(e))


def adjust_trade_quantity(crypto_account, symbol, side, quote_order_qty):
    """Adjust the trade quantity based on available balances. Assumes symbol format like 'BTCUSDT'."""
    try:
        # Derive base and quote assets assuming last 4 characters as quote asset
        base_asset, quote_asset = symbol[:-4], symbol[-4:]
        base_balance = get_account_balance(crypto_account, base_asset)["balance"]
        quote_balance = get_account_balance(crypto_account, quote_asset)["balance"]

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


def open_crypto_trade(crypto_account, symbol: str, side: str, quantity: float, custom_id: str = ''):
    """Open a new crypto trade via the Crypto.com API."""
    try:
        adjusted_quantity = adjust_trade_quantity(crypto_account, symbol, side, float(quantity))
        print("Adjusted quantity:", adjusted_quantity)

        order_params = {
            "instrument_name": symbol,
            "side": side.upper(),
            "type": "MARKET",  
            "quantity": adjusted_quantity,
            "client_oid": custom_id if custom_id else "", 
        }
        response = new_order(crypto_account.apiKey, crypto_account.secretKey, order_params)
        if response.get("code") != 0:
            raise ValueError(response.get("message", "Order placement failed"))
        order_data = response["data"]
        return {
            "order_id": order_data["order_id"],
            "symbol": symbol,
            "side": side.upper(),
            "price": order_data.get("price", "0"),
            "qty": adjusted_quantity,
        }
    except Exception as e:
        raise ValueError(str(e))


def close_crypto_trade(crypto_account, symbol: str, side: str, quantity: float):
    """Close an existing crypto trade by placing an opposite order via the Crypto.com API."""
    try:
        # Reverse the side for closing the position
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        adjusted_quantity = adjust_trade_quantity(crypto_account, symbol, t_side, float(quantity))
        
        order_params = {
            "instrument_name": symbol,
            "side": t_side.upper(),
            "type": "MARKET",  
            "quantity": adjusted_quantity,
        }
        response = new_order(crypto_account.apiKey, crypto_account.secretKey, order_params)
        if response.get("code") != 0:
            raise ValueError(response.get("message", "Order placement failed"))
        order_data = response["data"]
        return {
            "order_id": order_data["order_id"],
            "symbol": symbol,
            "side": t_side.upper(),
            "price": order_data.get("price", "0"),
            "qty": adjusted_quantity,
        }
    except Exception as e:
        raise ValueError(str(e))