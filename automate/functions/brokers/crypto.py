import hmac
import hashlib
import requests

from automate.functions.brokers.types import *
from automate.functions.brokers.broker import CryptoBrokerClient

class CryptoComClient(CryptoBrokerClient):

    BASE_URL = "https://api.crypto.com/exchange/v1/"

    @staticmethod
    def check_credentials(api_key, secret, account_type="S"):
        """Verify Crypto.com API credentials."""
        try:
            client = CryptoComClient(api_key=api_key, api_secret=secret, account_type=account_type)
            account_info = client.get_account_info()
            print("Account Info:", account_info)  # Debugging line to check the response
            if account_info.get("code") != 0:
                return {"error": account_info.get("message", "Invalid credentials"), "valid": False}
            return {"message": "API credentials are valid.", "valid": True}
        except Exception as e:
            return {"error": str(e)}

    def create_signature(self, req):
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
        return hmac.new(self.api_secret.encode('utf-8'), payload_str.encode('utf-8'), hashlib.sha256).hexdigest()

    def get_account_info(self):
        """Retrieve account information from Crypto.com Exchange API using JSON-RPC."""

        nonce = self._get_timestamp()
        payload = {
            "id": nonce,
            "method": "private/user-balance",
            "api_key": self.api_key,
            "params": {},
            "nonce": nonce
        }
        payload['sig'] = self.create_signature(payload)

        headers = {"Content-Type": "application/json"}
        response = requests.post(self.BASE_URL + payload["method"], json=payload, headers=headers)
        return response.json()
    

    def get_account_balance(self, symbol:str = None) -> AccountBalance:
        """Retrieve the balance for a specific asset from Crypto.com account info."""
        try:
            account_info = self.get_account_info()

            if account_info.get("code") != 0:
                raise ValueError(account_info.get("message", "Failed to retrieve account info"))
            balances = {}
            
            data = account_info["result"]["data"][0]
            # print("Balances Data:", data["position_balances"]) 
            
            for balance in data["position_balances"]:  # Debugging line to check each balance
                if symbol and balance["instrument_name"] not in symbol:
                    continue
                balances[balance["instrument_name"]] = float(balance["quantity"])
                balances[balance["instrument_name"]] = {
                    "available": float(balance["quantity"]),
                    "locked": 0.0
                }
                
            return balances

        except Exception as e:
            raise ValueError(str(e))

    def get_exchange_info(self, symbol) -> ExchangeInfo:
        """Retrieve exchange information for a specific symbol from Crypto.com Exchange API."""

        symbol = self.adjust_symbol_name(symbol)
        url = self.BASE_URL + f'public/get-instruments?instrument_name={symbol}'
        response = requests.get(url)

        res_json = response.json()    
        data_list = res_json.get('result', {}).get('data', [])
        
        target = symbol.upper()
        for sym in data_list:
            inst = sym.get('symbol', '')
            if inst.replace('_', '').upper() == target or inst == target:

                base_asset = sym.get('base_ccy')
                quote_asset = sym.get('quote_ccy')

                base_decimals = sym.get('quantity_decimals')
                quote_decimals = sym.get('quote_decimals')

                return {
                    'symbol': sym.get('symbol'),
                    'base_asset': base_asset,
                    'quote_asset': quote_asset,
                    'base_decimals': base_decimals,
                    'quote_decimals': quote_decimals,
                }
        return None


    def new_order(self, order_params):
        """Place a new order via the Crypto.com Exchange API using JSON-RPC."""
        nonce = self._get_timestamp()
        payload = {
            "id": nonce,
            "method": "private/create-order",
            "api_key": self.api_key,
            "params": order_params,
            "nonce": nonce
        }

        payload["sig"] = self.create_signature(payload)
        headers = {"Content-Type": "application/json"}

        response = requests.post(self.BASE_URL + payload["method"], json=payload, headers=headers)
        
        return response.json()


    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = '') -> OpenTrade:
        """Open a new crypto trade via the Crypto.com API."""
        try:

            symbol_info = self.get_exchange_info(symbol)
            if not symbol_info:
                raise Exception('Symbol was not found!')

            adjusted_quantity = self.adjust_trade_quantity(symbol_info, side, float(quantity))

            if float(adjusted_quantity) <= 0:
                raise ValueError("Insufficient quote balance.")

            print("Adjusted quantity:", adjusted_quantity)

            quote_asset = symbol_info.get('quote_asset')
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

            response = self.new_order(order_params)
            if response.get("code") != 0:
                raise ValueError(response.get("message", "Order placement failed"))
            
            # print("Order Response:", response)  # Debugging line to check the response
            order_data = response["result"]
            
            order_id = order_data["order_id"]
            order_details = self.get_order_info(symbol, order_id)

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
                    'message': f"Trade opened with order ID {order_id}.",
                    'order_id': order_id,
                    'symbol': symbol,
                    "side": side.upper(),
                    'qty': adjusted_quantity,
                    'price': order_data.get('price', '0'),
                    'currency': quote_asset,
                }
        
        except Exception as e:
            raise ValueError(str(e))

    def close_trade(self, symbol: str, side: str, quantity: float) -> CloseTrade:
        """Close an existing crypto trade by placing an opposite order via the Crypto.com API."""
        try:
            # Reverse the side for closing the position
            t_side = "SELL" if side.upper() == "BUY" else "BUY"
            
            symbol_info = self.get_exchange_info(symbol)
            if not symbol_info:
                raise Exception('Symbol was not found!')

            adjusted_quantity = self.adjust_trade_quantity(symbol_info, t_side, float(quantity))

            if float(adjusted_quantity) <= 0:
                raise ValueError("Insufficient quote balance.")
            
            order_symbol = symbol_info.get('symbol')

            
            order_params = {
                "instrument_name": order_symbol,
                "side": t_side.upper(),
                "type": "MARKET",  
                "quantity": str(adjusted_quantity),
            }

            response = self.new_order(order_params)
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

    def get_order_info(self, symbol, trade_id) -> OrderInfo:
        try:

            nonce = self._get_timestamp()
            payload = {
                "id": nonce,
                "method": "private/get-order-detail",
                "api_key": self.api_key,
                "params": {
                    "order_id": trade_id
                },
                "nonce": nonce
            }
            payload['sig'] = self.create_signature(payload)

            headers = {"Content-Type": "application/json"}
            response = requests.post(self.BASE_URL + payload["method"], json=payload, headers=headers)
            data = response.json()

            if data.get("code") == 0:
                result = data.get("result", {})
                
                # print(result)
                if result:
                    fees = float(result.get('cumulative_fee'))
                    fees = self.calculate_fees(str(result.get('instrument_name')), str(result.get('avg_price')), fees, str(result.get('fee_instrument_name')))


                    r = {
                        'order_id': str(result.get('order_id')),
                        'symbol': str(result.get('instrument_name')),
                        'volume': str(result.get('quantity')),
                        'side': str(result.get('side')),
                        'time': self.convert_timestamp(result.get('create_time')),
                        'price': str(result.get('avg_price')),

                        'fees': str(fees),

                        'additional_info': {
                            'order_value': str(result.get('order_value')),
                            'maker_fee_rate': str(result.get('maker_fee_rate')),
                            'taker_fee_rate': str(result.get('taker_fee_rate')),
                            'fees_currency': str(result.get('fee_instrument_name')),
                        }
                    }
                    return r
            
            return None
            
        except Exception as e:
            print('Error get crypto order details, ', e)
            return None


    def get_current_price(self, symbol):
        """Fetch the current market price for a given symbol from Crypto.com Exchange API."""
        try:
            url = self.BASE_URL + f'public/get-tickers?instrument_name={symbol}'
            response = requests.get(url)
            res_json = response.json()
            data_list = res_json.get('result', {}).get('data', [])
            
            target = symbol.upper()

            # print(res_json)
            for sym in data_list:
                inst = sym.get('i', '')
                if inst.replace('_', '').upper() == target or inst == target:
                    return float(sym.get('a'))  # Return the ask price as the current price
            return None
        except Exception as e:
            print("Error fetching exchange price:", e)
            return None
        
    def get_trading_pairs(self):
        """Retrieve a list of all trading pairs available on Crypto.com Exchange."""
        try:
            url = self.BASE_URL + 'public/get-instruments'
            response = requests.get(url)
            res_json = response.json()
            data_list = res_json.get('result', {}).get('data', [])
            
            trading_pairs = [sym.get('symbol') for sym in data_list if 'symbol' in sym]
            return trading_pairs
        except Exception as e:
            print("Error fetching trading pairs:", e)
            return []
        
    def get_history_candles(self, symbol, interval, limit = 500):
        """Fetch historical candlestick data for a given symbol and interval from Crypto.com Exchange API."""
        try:
            url = self.BASE_URL + f'public/get-candlestick?instrument_name={symbol}&timeframe={interval}&limit={limit}'
            response = requests.get(url)
            res_json = response.json()
            data_list = res_json.get('result', {}).get('data', [])
            
            candles = []
            for candle in data_list:
                candles.append({
                    'open': float(candle.get('o')),
                    'high': float(candle.get('h')),
                    'low': float(candle.get('l')),
                    'close': float(candle.get('c')),
                    'volume': float(candle.get('v')),
                    'time': self.convert_timestamp(candle.get('t')),
                })
            return candles
        except Exception as e:
            print("Error fetching historical candles:", e)
            return []
        
    def get_order_book(self, symbol, limit=10):
        """Fetch the order book for a given symbol from Crypto.com Exchange API."""
        try:
            if limit > 50:
                limit = 50
            url = self.BASE_URL + f'public/get-book?instrument_name={symbol}&depth={limit}'
            response = requests.get(url)
            res_json = response.json()
            data = res_json.get('result', {}).get('data', {})

            if isinstance(data, list):
                data = data[0] if data else {}
            
            order_book = {
                'bids': [(float(bid[0]), float(bid[1])) for bid in data.get('bids', [])],
                'asks': [(float(ask[0]), float(ask[1])) for ask in data.get('asks', [])],
            }
            return order_book
        except Exception as e:
            print("Error fetching order book:", e)
            return {'bids': [], 'asks': []}