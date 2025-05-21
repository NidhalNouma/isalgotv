import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP


from .broker import BrokerClient

class MexcClient(BrokerClient):
    BASE_URL = 'https://api.mexc.com'
    FUTURES_BASE_URL = 'https://contract.mexc.com'

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
    def check_credentials(api_key, api_secret, account_type="S"):
        try:
            client = MexcClient(api_key=api_key, api_secret=api_secret, account_type=account_type)
            if account_type == "S":
                # Check spot account info
                account_info = client.get_account_info()
            elif account_type == "F":
                # Check futures account info
                account_info = client.get_futures_account_info()

            # Assuming a successful response returns a code of 200
            if not account_info:
                return {"error": account_info.get("message", "Invalid credentials"), "valid": False}
            return {"message": "API credentials are valid.", "valid": True}
        except Exception as e:
            return {"error": str(e)}

        
    def _get_timestamp(self):
        return int(time.time() * 1000)


    def create_signature(self, query_string):
        return hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def send_request(self, method, endpoint, params=None):
        if params is None:
            params = {}

        params["timestamp"] = self._get_timestamp()
        query_string = urlencode(params)
        signature = self.create_signature(query_string)
        params["signature"] = signature
        headers = {
            "X-MEXC-APIKEY": self.api_key,
            "Content-Type": "application/json"
        }

        url = f"{self.BASE_URL}{endpoint}"


        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, params=params)
        else:
            raise ValueError("Unsupported HTTP method")

        data = response.json()
        if response.status_code != 200:
            raise ValueError(f"{data.get('msg')}")

        if isinstance(data, dict) and data.get("code", 0) != 0:
            raise ValueError(f"{data.get('message')}")

        return data

    def send_futures_request(self, method, endpoint, params=None):
        if params is None:
            params = {}

        timestamp = str(self._get_timestamp())
        signature_target = self.api_key + timestamp
        signature = hmac.new(self.api_secret.encode("utf-8"), signature_target.encode("utf-8"), hashlib.sha256).hexdigest()
        
        headers = {
            "ApiKey": self.api_key,
            "Request-Time": timestamp,
            "Signature": signature,
            "Content-Type": "application/json"
        }

        url = f"{self.FUTURES_BASE_URL}{endpoint}"

        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, params=params)
        else:
            raise ValueError("Unsupported HTTP method")
        
        data = response.json()
        if response.status_code != 200:
            raise ValueError(f"{data.get('msg')}")
        if isinstance(data, dict) and data.get("code", 0) != 0:
            raise ValueError(f"{data.get('message')}")
        return data


    def get_account_info(self):
        endpoint = "/api/v3/account"
        response_data = self.send_request('GET', endpoint)
        
        return response_data

    def get_account_balance(self):
        try:
            account_info = self.get_account_info()
            
            balances = {}
            # Expected structure:
            # {"code":200, "data": {"balances": [{"asset": "BTC", "free": "0.1", ...}, ...]}}
            for balance in account_info["balances"]:
                balances[balance["asset"]] = float(balance["free"])
                
            return balances
        except Exception as e:
            raise ValueError(str(e))

    def get_futures_account_info(self):
        """Retrieve futures account information using MEXC futures API."""
        print("Getting futures account info...")
        endpoint = "/api/v1/private/account/assets"

        response_data = self.send_futures_request('GET', endpoint)
        return response_data

    def get_exchange_info(self, symbol):
        params = {
            "symbol": symbol
        }

        if self.account_type == "F":
            endpoint = "/api/v1/contract/detail"
            response_data = self.send_futures_request('GET', endpoint, params)
                    
            if isinstance(response_data, dict) and response_data.get("data"):
                symbols = response_data.get("data")
                return symbols

        else:
            endpoint = "/api/v3/exchangeInfo"
            response_data = self.send_request('GET', endpoint, params)

            if isinstance(response_data, dict) and response_data.get("symbols"):
                symbols = response_data.get("symbols")
                for s in symbols:
                    if s.get("symbol") == symbol:
                        return s
                    
    
        if isinstance(response_data, list):
            for s in response_data:
                if s.get("symbol") == symbol:
                    return s
        
        raise Exception('Symbol was not found!')
        

    def new_order(self, order_params):
        endpoint = "/api/v3/order"
        
        response_data = self.send_request('POST', endpoint, order_params)

        return response_data


    def new_futures_order(self, order_params):
        """Place a new futures order using MEXC futures API."""
        endpoint = "/api/v1/private/order/submit"

        response_data = self.send_futures_request('POST', endpoint, order_params)
        print("Futures order response:", response_data)
        
        return response_data
        

    def adjust_trade_quantity(self, exchange_info, side, quote_order_qty):
        try:
            base_asset, quote_asset = exchange_info.get("baseAsset"), exchange_info.get("quoteAsset")
            if not base_asset or not quote_asset:
                raise ValueError("Invalid symbol format or exchange info not found.")
            
            balances = self.get_account_balance()
            
            base_balance = balances.get(base_asset, 0)
            quote_balance = balances.get(quote_asset, 0)

            base_decimals = exchange_info.get('baseAssetPrecision') 
            quote_decimals = exchange_info.get('quoteAssetPrecision') 

            print("Base asset:", base_asset, base_decimals)
            print("Quote asset:", quote_asset, quote_decimals)

            print("Base balance:", base_balance)
            print("Quote balance:", quote_balance)

            try:
                precision = int(base_decimals)
            except (TypeError, ValueError):
                precision = 8  # fallback precision
            quant = Decimal(1).scaleb(-precision)  


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
        except Exception as e:
            raise ValueError(str(e))


    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None):
        try:
            if self.account_type == "F":
                return self.open_mexc_futures_trade(symbol, side, quantity, custom_id)
            
            sys_info = self.get_exchange_info(symbol)
            
            currency_asset = sys_info.get('quoteAsset')
            base_asset = sys_info.get('baseAsset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity = self.adjust_trade_quantity(sys_info, side, float(quantity))
            # adjusted_quantity = quantity
            print("Adjusted quantity:", adjusted_quantity)

            
            order_params = {
                "symbol": order_symbol,
                "side": side.upper(),
                "type": "MARKET",  # Using lowercase as per MEXC docs
                "quantity": adjusted_quantity,
            }
            response = self.new_order(order_params)
            
            order_data = response

            order_id = order_data["orderId"]

            if not self.current_trade:
                order_details = self.get_order_info(order_symbol, order_id)
                trade_details = None 
            else :
                order_details = self.get_final_trade_details(self.current_trade, order_id)
                trade_details = order_details
            
            if order_details:
                return {
                    'message': f"Trade opened with order ID {order_id}.",
                    'order_id': order_id,
                    'closed_order_id': order_id,
                    'symbol': order_symbol,
                    "side": side.upper(),
                    'qty': order_details.get('volume', adjusted_quantity),
                    'price': order_details.get('price', '0'),
                    'time': order_details.get('time', ''),
                    'fees': order_details.get('fees', ''),
                    'currency': currency_asset,

                    'trade_details': trade_details
                }
            
            else:
                return {
                    'message': f"Trade opened with order ID {order_id}.",
                    'order_id': order_id,
                    'closed_order_id': order_id,
                    'symbol': order_symbol,
                    "side": side.upper(),
                    'price': order_data.get('price', '0'),
                    'time': self.convert_timestamp(order_data.get('time', '')),
                    'qty': adjusted_quantity,
                    'currency': currency_asset,
                }
        except Exception as e:
            raise ValueError(str(e))


    def close_trade(self, symbol: str, side: str, quantity: float):
        try:
            if self.account_type == "F":
                return self.close_mexc_futures_trade(symbol, side, quantity)
            
            t_side = "SELL" if side.upper() == "BUY" else "BUY"
            return self.open_trade(symbol, t_side, quantity)
        except Exception as e:
            raise ValueError(str(e))

    def open_mexc_futures_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None):
        """Open a new futures trade on MEXC. Note: futures orders may require additional parameters such as leverage and margin type."""

        t_side = 1 if side.upper() == "BUY" else 3

        sys_info = self.get_exchange_info(symbol)

        # print(sys_info)
        
        currency_asset = sys_info.get('quoteAsset')
        base_asset = sys_info.get('baseAsset')
        order_symbol = sys_info.get('symbol')


        try:
            order_params = {
                "symbol": symbol,
                "side": t_side,
                "type": 5,
                "vol": quantity,
            }
            print("Order params:", order_params)

            response = self.new_futures_order(order_params)
            
            order_id = response["data"]
            return {
                "order_id": order_id,
                "symbol": symbol,
                "side": side.upper(),
                "price": 0,
                "qty": quantity,
            }
        except Exception as e:
            raise ValueError(str(e))


    def close_mexc_futures_trade(self, symbol: str, side: str, quantity: float):
        """Close an existing futures trade on MEXC by placing an opposite order."""
        try:
            # Reverse the side for closing the position
            t_side = 4 if side.upper() == "BUY" else 2
            order_params = {
                "symbol": symbol,
                "side": t_side,
                "type": 5,
                "vol": quantity,
                "reduceOnly": "true",
            }
            response = self.new_futures_order(order_params)
            if response.get("code") != 200:
                raise ValueError(response.get("message", "Futures order placement failed"))
            order_id = response["data"]
            return {
                "order_id": order_id,
                "symbol": symbol,
                "side": t_side.upper(),
                "price": 0,
                "qty": quantity,
            }
        except Exception as e:
            raise ValueError(str(e))

        
    def get_order_info(self, symbol, order_id):
        try:
            if self.account_type == "F":
                return self.get_future_order_info(symbol, order_id)

            endpoint = "/api/v3/myTrades"
            params = {
                "symbol": symbol,
                "orderId": order_id,
            }

            response = self.send_request('GET', endpoint, params)

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

            sym_info = self.get_exchange_info(symbol)

            fees = float(trade.get('commission'))
            # Convert fees from ADA to USDT using avg_price

            if str(trade.get('commissionAsset')) == sym_info.get('baseAsset'):
                try:
                    fee_ada = Decimal(str(fees))
                    price_usdt = Decimal(str(trade.get('price', '0')))
                    fees = fee_ada * price_usdt
                except (InvalidOperation, ValueError):
                    pass
            
            dt_aware = self.convert_timestamp(trade.get('time'))

            
            r = {
                'order_id': str(trade.get('orderId')),
                'symbol': str(trade.get('symbol')),
                'volume': str(trade.get('qty')),
                'side': str(trade.get('side')),
                
                'time': dt_aware,
                'price': str(trade.get('price')),

                'fees': str(fees),

                'additional_info': {
                    'commission': str(trade.get('commission')),
                    'commissionAsset': str(trade.get('commissionAsset')),
                },
            }

            return r
        except Exception as e:     
            print('getting trade info ', e)   
            return None

        
    def get_future_order_info(self, symbol, order_id):
        try:
            endpoint =f"/api/v1/private/order/get/{order_id}"

            params = {
                "orderId": order_id,
            }

            response = self.send_futures_request('GET', endpoint, params)

            # print("Order info response:", response)
            response = response.get('data')
            
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

            sym_info = self.get_exchange_info(symbol)

            fees = float(trade.get('takerFee'))
            # Convert fees from ADA to USDT using avg_price

            if str(trade.get('feeCurrency')) == sym_info.get('baseCoin'):
                try:
                    fee_ada = Decimal(str(fees))
                    price_usdt = Decimal(str(trade.get('price', '0')))
                    fees = fee_ada * price_usdt
                except (InvalidOperation, ValueError):
                    pass
            
            
            dt_aware = self.convert_timestamp(trade.get('createTime'))
            
            r = {
                'order_id': str(trade.get('orderId')),
                'symbol': str(trade.get('symbol')),
                'volume': str(trade.get('vol')),
                'side': str(trade.get('side')),
                
                'time': dt_aware,
                'price': str(trade.get('price')),

                'fees': str(fees),
                'profit': str(trade.get('profit')),

                'additional_info': {
                    'commission': str(trade.get('takerFee')),
                    'commissionAsset': str(trade.get('feeCurrency')),
                }

            }

            return r
        except Exception as e:     
            print('getting trade info ', e)   
            return None
        
