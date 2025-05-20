import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

class MexcClient:
    BASE_URL = 'https://api.bybit.com/v5'

    def __init__(self, account=None, api_key=None, api_secret=None, account_type="S", current_trade=None):

        if account is not None:
            self.api_key = account.apiKey
            self.api_secret = account.secretKey
            self.account_type = getattr(account, 'accountType', None) or getattr(account, 'type', None)
        else:
            self.api_key = api_key
            self.api_secret = api_secret
            self.account_type = account_type
        self.current_trade = current_trade
        
    
    @staticmethod
    def check_mexc_credentials(api_key, api_secret, account_type="S"):
        try:
            client = MexcClient(api_key=api_key, api_secret=api_secret, account_type=account_type)
            if account_type == "S":
                # Check spot account info
                account_info = client.get_account_info()
            elif account_type == "F":
                # Check futures account info
                account_info = client.get_futures_account_info()

            # Assuming a successful response returns a code of 200
            if account_info.get("code") != 200:
                return {"error": account_info.get("message", "Invalid credentials"), "valid": False}
            return {"message": "API credentials are valid.", "valid": True}
        except Exception as e:
            return {"error": str(e)}

        
    def _get_timestamp(self):
        return int(time.time() * 1000)


    def create_signature(self, query_string):
        return hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()


    def get_account_info(self):
        endpoint = "/api/v3/account"
        params = {
            "timestamp": _get_timestamp()
        }
        query_string = urlencode(params)
        signature = self.create_signature(query_string)
        params["signature"] = signature
        headers = {
            "X-MEXC-APIKEY": self.api_key,
            "Content-Type": "application/json"
        }
        response = requests.get(BASE_URL + endpoint, params=params, headers=headers)
        response_data = response.json()
        response_data['code'] = response.status_code
        return response_data

    def get_futures_account_info(self):
        """Retrieve futures account information using MEXC futures API."""
        print("Getting futures account info...")
        endpoint = "/api/v1/private/account/assets"

        timestamp = str(_get_timestamp())
        signature_target = self.api_key + timestamp
        signature = hmac.new(self.api_secret.encode("utf-8"), signature_target.encode("utf-8"), hashlib.sha256).hexdigest()
        
        headers = {
            "ApiKey": self.api_key,
            "Request-Time": timestamp,
            "Signature": signature,
            "Content-Type": "application/json"
        }

        response = requests.get(FUTURES_BASE_URL + endpoint, headers=headers)

        response_data = response.json()
        response_data['code'] = response.status_code
        
        return response_data

    def get_exchange_info(self, symbol):
        endpoint = "/api/v3/exchangeInfo"
        params = {
            "timestamp": _get_timestamp(),
            "symbol": symbol
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.get(BASE_URL + endpoint, params=params, headers=headers)
        response_data = response.json()
        response_data['code'] = response.status_code
        return response_data
    

    def new_order(self, order_params):
        endpoint = "/api/v3/order"
        order_params["timestamp"] = self._get_timestamp()
        query_string = urlencode(order_params)
        signature = self.create_signature(query_string)
        order_params["signature"] = signature
        headers = {
            "X-MEXC-APIKEY": self.api_key,
            "Content-Type": "application/json"
        }
        response = requests.post(BASE_URL + endpoint, data=order_params, headers=headers)  
        print("Order response:", response, response.json())  
        response_data = response.json()

        if "code" not in response_data:
            response_data["code"] = response.status_code
        return response_data


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
        "X-MEXC-APIKEY": api_key,
        "Content-Type": "application/json"
    }
    response = requests.get(BASE_URL + endpoint, params=params, headers=headers)
    response_data = response.json()
    response_data['code'] = response.status_code
    return response_data

def get_exchange_info(symbol):
    endpoint = "/api/v3/exchangeInfo"
    params = {
        "timestamp": _get_timestamp(),
        "symbol": symbol
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.get(BASE_URL + endpoint, params=params, headers=headers)
    response_data = response.json()
    response_data['code'] = response.status_code
    return response_data


def new_order(api_key, secret, order_params):
    endpoint = "/api/v3/order"
    order_params["timestamp"] = _get_timestamp()
    query_string = urlencode(order_params)
    signature = create_signature(query_string, secret)
    order_params["signature"] = signature
    headers = {
        "X-MEXC-APIKEY": api_key,
        "Content-Type": "application/json"
    }
    response = requests.post(BASE_URL + endpoint, data=order_params, headers=headers)  
    print("Order response:", response, response.json())  
    response_data = response.json()

    if "code" not in response_data:
        response_data["code"] = response.status_code
    return response_data


def check_mexc_credentials(api_key, api_secret, trade_type="S"):
    try:
        if trade_type == "S":
            # Check spot account info
            account_info = get_account_info(api_key, api_secret)
        elif trade_type == "F":
            # Check futures account info
            account_info = get_futures_account_info(api_key, api_secret)

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
        for balance in account_info["balances"]:
            balances[balance["asset"]] = float(balance["free"])
        return {"asset": asset, "balance": balances.get(asset, 0.0)}
    except Exception as e:
        raise ValueError(str(e))


def adjust_trade_quantity(mexc_account, symbol, side, quote_order_qty):
    try:
        
        exchange_info = get_exchange_info(symbol)
        # print("Exchange info:", exchange_info)
        if exchange_info.get("code") != 200:
            raise ValueError("Failed to retrieve exchange info")
        
        base_asset, quote_asset = exchange_info["symbols"][0]["baseAsset"], exchange_info["symbols"][0]["quoteAsset"]
        if not base_asset or not quote_asset:
            raise ValueError("Invalid symbol format or exchange info not found.")
        
        
        base_balance = get_account_balance(mexc_account, base_asset)["balance"]
        quote_balance = get_account_balance(mexc_account, quote_asset)["balance"]

        print("Base asset:", base_asset)
        print("Quote asset:", quote_asset)
        print("Base balance:", base_balance)
        print("Quote balance:", quote_balance)

        if side.upper() == "BUY":
            if quote_balance <= 0:
                raise ValueError("Insufficient quote balance.")
            elif quote_balance < quote_order_qty:
                return quote_balance
        elif side.upper() == "SELL":
            if base_balance <= 0:
                raise ValueError("Insufficient base balance.")
            elif base_balance < quote_order_qty:
                return base_balance
        return quote_order_qty
    except Exception as e:
        raise ValueError(str(e))


def open_mexc_trade(mexc_account, symbol: str, side: str, quantity: float, custom_id: str = None):
    try:
        if mexc_account.type == "F":
            return open_mexc_futures_trade(mexc_account, symbol, side, quantity, custom_id)
        

        adjusted_quantity = adjust_trade_quantity(mexc_account, symbol, side, float(quantity))
        # adjusted_quantity = quantity
        print("Adjusted quantity:", adjusted_quantity)

        
        order_params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",  # Using lowercase as per MEXC docs
            "quantity": adjusted_quantity,
        }
        response = new_order(mexc_account.apiKey, mexc_account.secretKey, order_params)
        
        if response.get("code") != 200:
            raise ValueError(response.get("msg", "Order placement failed"))
        order_data = response
        
        return {
            "order_id": order_data["orderId"],
            "symbol": symbol,
            "side": side.upper(),
            "price": order_data["price"] if "price" in order_data else "0",  # Market orders typically don't have a set price
            "qty": adjusted_quantity,
        }
    except Exception as e:
        raise ValueError(str(e))


def close_mexc_trade(mexc_account, symbol: str, side: str, quantity: float):
    try:
        if mexc_account.type == "F":
            return close_mexc_futures_trade(mexc_account, symbol, side, quantity)
        
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        adjusted_quantity = adjust_trade_quantity(mexc_account, symbol, t_side, float(quantity))

        order_params = {
            "symbol": symbol,
            "side": t_side.upper(),
            "type": "MARKET",
            "quantity": adjusted_quantity,
        }
        response = new_order(mexc_account.apiKey, mexc_account.secretKey, order_params)
        if response.get("code") != 200:
            raise ValueError(response.get("msg", "Order placement failed"))
        order_data = response
        
        return {
            "order_id": order_data["orderId"],
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
    print("Getting futures account info...")
    endpoint = "/api/v1/private/account/assets"

    timestamp = str(_get_timestamp())
    signature_target = api_key + timestamp
    signature = hmac.new(secret.encode("utf-8"), signature_target.encode("utf-8"), hashlib.sha256).hexdigest()
    
    headers = {
        "ApiKey": api_key,
        "Request-Time": timestamp,
        "Signature": signature,
        "Content-Type": "application/json"
    }

    response = requests.get(FUTURES_BASE_URL + endpoint, headers=headers)

    response_data = response.json()
    response_data['code'] = response.status_code
    
    return response_data



def new_futures_order(api_key, secret, order_params):
    """Place a new futures order using MEXC futures API."""
    endpoint = "api/v1/private/order/submit"

    timestamp = str(_get_timestamp())
    signature_target = api_key + timestamp
    signature = hmac.new(secret.encode("utf-8"), signature_target.encode("utf-8"), hashlib.sha256).hexdigest()
    

    # order_params["timestamp"] = timestamp
    # query_string = urlencode(order_params)
    # signature = create_signature(query_string, secret)
    # order_params["signature"] = signature
 
    headers = {
        "ApiKey": api_key,
        "Request-Time": timestamp,
        "Signature": signature,
        "Content-Type": "application/json"
    }

    response = requests.post(FUTURES_BASE_URL + endpoint, data=order_params, headers=headers)
    
    response_data = response.json()
    if "code" not in response_data:
        response_data['code'] = response.status_code
    print("Futures order response:", response_data)
    
    return response_data


def open_mexc_futures_trade(mexc_account, symbol: str, side: str, quantity: float, custom_id: str = None):
    """Open a new futures trade on MEXC. Note: futures orders may require additional parameters such as leverage and margin type."""

    t_side = 1 if side.upper() == "BUY" else 3
    try:
        order_params = {
            "symbol": symbol,
            "side": t_side,
            "type": 5,
            "vol": quantity,
        }
        print("Order params:", order_params)

        response = new_futures_order(mexc_account.apiKey, mexc_account.secretKey, order_params)
        if response.get("code") != 200:
            raise ValueError(response.get("message", "Futures order placement failed"))
        order_data = response["data"]
        return {
            "order_id": order_data,
            "symbol": symbol,
            "side": side.upper(),
            "price": 0,
            "qty": quantity,
        }
    except Exception as e:
        raise ValueError(str(e))


def close_mexc_futures_trade(mexc_account, symbol: str, side: str, quantity: float):
    """Close an existing futures trade on MEXC by placing an opposite order."""
    try:
        # Reverse the side for closing the position
        t_side = 4 if side.upper() == "BUY" else 2
        order_params = {
            "symbol": symbol,
            "side": t_side,
            "type": 5,
            "vol": quantity,
        }
        response = new_futures_order(mexc_account.apiKey, mexc_account.secretKey, order_params)
        if response.get("code") != 200:
            raise ValueError(response.get("message", "Futures order placement failed"))
        order_data = response["data"]
        return {
            "order_id": order_data,
            "symbol": symbol,
            "side": t_side.upper(),
            "price": 0,
            "qty": quantity,
        }
    except Exception as e:
        raise ValueError(str(e))