import requests
from urllib.parse import urlencode

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

class MexcClient(CryptoBrokerClient):
    BASE_URL = 'https://api.mexc.com'
    FUTURES_BASE_URL = 'https://contract.mexc.com'
    
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

    def _send_request(self, method, endpoint, params=None):
        if params is None:
            params = {}

        params["timestamp"] = self._get_timestamp()
        query_string = urlencode(params)
        signature = self._create_signature(query_string)
        params["signature"] = signature
        headers = {
            "X-MEXC-APIKEY": self.api_key,
            "Content-Type": "application/json"
        }

        url = f"{self.BASE_URL}{endpoint}"


        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=5)
        elif method == 'POST':
            response = requests.post(url, headers=headers, params=params, timeout=5)
        else:
            raise ValueError("Unsupported HTTP method")

        data = response.json()
        if response.status_code != 200:
            raise ValueError(f"{data.get('msg')}")

        if isinstance(data, dict) and data.get("code", 0) != 0:
            raise ValueError(f"{data.get('message')}")

        return data

    def _send_futures_request(self, method, endpoint, params=None):
        if params is None:
            params = {}

        timestamp = str(self._get_timestamp())
        signature_target = self.api_key + timestamp
        signature = self._create_signature(signature_target)
        
        headers = {
            "ApiKey": self.api_key,
            "Request-Time": timestamp,
            "Signature": signature,
            "Content-Type": "application/json"
        }

        url = f"{self.FUTURES_BASE_URL}{endpoint}"

        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=5)
        elif method == 'POST':
            response = requests.post(url, headers=headers, params=params, timeout=5)
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
        response_data = self._send_request('GET', endpoint)
        
        return response_data

    def get_account_balance(self, symbol:str = None) -> AccountBalance:
        try:
            account_info = self.get_account_info()
            
            balances = {}
            # Expected structure:
            # {"code":200, "data": {"balances": [{"asset": "BTC", "free": "0.1", ...}, ...]}}
            for balance in account_info["balances"]:
                if symbol and balance["asset"] not in symbol:
                    continue
                balances[balance["asset"]] = float(balance["free"])
                balances[balance["asset"]] = {
                    "available": float(balance["free"]),
                    "locked": float(balance["locked"])
                }
                
            return balances
        except Exception as e:
            raise ValueError(str(e))

    def get_futures_account_info(self):
        """Retrieve futures account information using MEXC futures API."""
        print("Getting futures account info...")
        endpoint = "/api/v1/private/account/assets"

        response_data = self._send_futures_request('GET', endpoint)
        return response_data

    def get_exchange_info(self, symbol) -> ExchangeInfo:

        symbol = self.adjust_symbol_name(symbol)
        params = {
            "symbol": symbol
        }

        if self.account_type == "F":
            endpoint = "/api/v1/contract/detail"
            response_data = self._send_futures_request('GET', endpoint, params)
                    
            if isinstance(response_data, dict) and response_data.get("data"):
                s = response_data.get("data")
                if s.get("symbol") == symbol:

                    return {
                        "symbol": symbol,
                        "base_asset": s.get("baseCoin"),
                        "quote_asset": s.get("quoteCoin"),
                        "base_decimals": self.get_decimals_from_step(s.get("minVol")),
                        "quote_decimals": self.get_decimals_from_step(s.get("minVol")),
                    }

        else:
            endpoint = "/api/v3/exchangeInfo"
            response_data = self._send_request('GET', endpoint, params)

            # print("Exchange info response:", response_data)

            if isinstance(response_data, dict) and response_data.get("symbols"):
                symbols = response_data.get("symbols")
                for s in symbols:
                    if s.get("symbol") == symbol:

                        return {
                            "symbol": symbol,
                            "base_asset": s.get("baseAsset"),
                            "quote_asset": s.get("quoteAsset"),
                            "base_decimals": s.get("baseAssetPrecision"),
                            "quote_decimals": s.get("quoteAssetPrecision"),
                        }
                    
    
        if isinstance(response_data, list):
            for s in response_data:
                if s.get("symbol") == symbol:
                    return {
                        "symbol": symbol,
                        "base_asset": s.get("baseAsset"),
                        "quote_asset": s.get("quoteAsset"),
                        "base_decimals": s.get("baseAssetPrecision"),
                        "quote_decimals": s.get("quoteAssetPrecision"),
                    }
        
        raise Exception('Symbol was not found!')
        

    def _new_order(self, order_params):
        endpoint = "/api/v3/order"
        
        response_data = self._send_request('POST', endpoint, order_params)

        return response_data


    def _new_futures_order(self, order_params):
        """Place a new futures order using MEXC futures API."""
        endpoint = "/api/v1/private/order/submit"

        response_data = self._send_futures_request('POST', endpoint, order_params)
        print("Futures order response:", response_data)
        
        return response_data
        

    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None) -> OpenTrade:
        try:
            print("Opening spot trade...")
            if self.account_type == "F":
                return self.open_mexc_futures_trade(symbol, side, quantity, custom_id)
            sys_info = self.get_exchange_info(symbol)
            
            currency_asset = sys_info.get('quote_asset')
            base_asset = sys_info.get('base_asset')
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
            response = self._new_order(order_params)
            
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


    def close_trade(self, symbol: str, side: str, quantity: float) -> CloseTrade:
        try:
            if self.account_type == "F":
                return self.close_mexc_futures_trade(symbol, side, quantity)
            
            t_side = "SELL" if side.upper() == "BUY" else "BUY"
            return self.open_trade(symbol, t_side, quantity)
        except Exception as e:
            raise ValueError(str(e))

    def open_mexc_futures_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None) -> OpenTrade:
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

            response = self._new_futures_order(order_params)
            
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


    def close_mexc_futures_trade(self, symbol: str, side: str, quantity: float) -> CloseTrade:
        """Close an existing futures trade on MEXC by placing an opposite order."""
        try:
            symbol = self.adjust_symbol_name(symbol)
            # Reverse the side for closing the position
            t_side = 4 if side.upper() == "BUY" else 2
            order_params = {
                "symbol": symbol,
                "side": t_side,
                "type": 5,
                "vol": quantity,
                "reduceOnly": "true",
            }
            response = self._new_futures_order(order_params)
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

        
    def get_order_info(self, symbol, order_id) -> OrderInfo:
        try:
            if self.account_type == "F":
                return self.get_future_order_info(symbol, order_id)

            endpoint = "/api/v3/myTrades"
            params = {
                "symbol": symbol,
                "orderId": order_id,
            }

            response = self._send_request('GET', endpoint, params)

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

            fees = float(trade.get('commission'))
            fees = self.calculate_fees(symbol, trade.get('price', '0'), fees, trade.get('commissionAsset'))

            r = {
                'order_id': str(trade.get('orderId')),
                'symbol': str(trade.get('symbol')),
                'volume': str(trade.get('qty')),
                'side': str(trade.get('side')),
                
                'time': self.convert_timestamp(trade.get('time')),
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

        
    def get_future_order_info(self, symbol, order_id) -> OrderInfo:
        try:
            endpoint =f"/api/v1/private/order/get/{order_id}"

            params = {
                "orderId": order_id,
            }

            response = self._send_futures_request('GET', endpoint, params)

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

            fees = float(trade.get('takerFee'))
            fees = self.calculate_fees(symbol, trade.get('price', '0'), fees, trade.get('feeCurrency'))
            
            r = {
                'order_id': str(trade.get('orderId')),
                'symbol': str(trade.get('symbol')),
                'volume': str(trade.get('vol')),
                'side': str(trade.get('side')),
                
                'time': self.convert_timestamp(trade.get('createTime')),
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

    # ------------------------------------------------------------------------------------------------------------------------
    # methods for market data
    # ------------------------------------------------------------------------------------------------------------------------

    def get_trading_pairs(self) -> List[str]:
        try:
            if self.account_type == "F":
                return self.get_futures_trading_pairs()

            endpoint = "/api/v3/exchangeInfo"
            response = self._send_request('GET', endpoint)
            symbols = []
            if isinstance(response, dict) and response.get("symbols"):
                for s in response.get("symbols"):
                    symbols.append(s.get("symbol"))
            return symbols
        except Exception as e:
            raise ValueError(str(e))
        
    def get_futures_trading_pairs(self) -> List[str]:
        try:
            endpoint = "/api/v1/contract/detail"
            response = self._send_futures_request('GET', endpoint)
            # print(response)
            data = response.get("data", [])
            symbols = []
            if isinstance(data, list):
                for s in data:
                    symbols.append(s.get("symbol"))
            return symbols
        except Exception as e:
            raise ValueError(str(e))
    
    def get_history_candles(self, symbol, interval, limit=100):
        try:
            if interval not in ["1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d","3d","1w","1M"]:
                raise ValueError(f"Invalid interval: {interval}")
            
            if self.account_type == "F":
                return self.get_future_history_candles(symbol, interval, limit=limit)
            
            endpoint = "/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = self._send_request('GET', endpoint, params)
            candles = []
            if isinstance(response, list):
                for item in response:
                    candle = {
                        "timestamp": self.convert_timestamp(item[0]),
                        "open": str(item[1]),
                        "high": str(item[2]),
                        "low": str(item[3]),
                        "close": str(item[4]),
                        "volume": str(item[5])
                    }
                    candles.append(candle)
            return candles
        except Exception as e:
            raise ValueError(str(e))

    def get_future_history_candles(self, symbol, interval, limit=100):
        try:
            if interval not in ["1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d","3d","1w","1M"]:
                raise ValueError(f"Invalid interval: {interval}")
            
            endpoint = "/api/v1/contract/kline"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = self._send_futures_request('GET', endpoint, params)
            # print(response)
            data = response.get("data", [])
            candles = []
            if isinstance(data, list):
                for item in data:
                    candle = {
                        "timestamp": self.convert_timestamp(item[0]),
                        "open": str(item[1]),
                        "high": str(item[2]),
                        "low": str(item[3]),
                        "close": str(item[4]),
                        "volume": str(item[5])
                    }
                    candles.append(candle)
            return candles
        except Exception as e:
            raise ValueError(str(e))

    def get_order_book(self, symbol, limit=100):
        try:
            if limit not in [5, 10, 20, 50, 100, 500, 1000, 5000]:
                raise ValueError(f"Invalid limit: {limit}")
            
            if self.account_type == "F":
                return self.get_futures_order_book(symbol, limit=limit)
            
            endpoint = "/api/v3/depth"
            params = {
                "symbol": symbol,
                "limit": limit
            }
            response = self._send_request('GET', endpoint, params)
            order_book = {
                "bids": [],
                "asks": []
            }
            if isinstance(response, dict):
                for bid in response.get("bids", []):
                    order_book["bids"].append({
                        "price": str(bid[0]),
                        "quantity": str(bid[1])
                    })
                for ask in response.get("asks", []):
                    order_book["asks"].append({
                        "price": str(ask[0]),
                        "quantity": str(ask[1])
                    })
            return order_book
        except Exception as e:
            raise ValueError(str(e))

    def get_futures_order_book(self, symbol, limit=100):
        try:
            if limit not in [5, 10, 20, 50, 100, 500, 1000, 5000]:
                raise ValueError(f"Invalid limit: {limit}")
            
            endpoint = "/api/v1/contract/depth"
            params = {
                "symbol": symbol,
                "limit": limit
            }
            response = self._send_futures_request('GET', endpoint, params)
            # print(response)
            data = response.get("data", {})
            order_book = {
                "bids": [],
                "asks": []
            }
            if isinstance(data, dict):
                for bid in data.get("bids", []):
                    order_book["bids"].append({
                        "price": str(bid[0]),
                        "quantity": str(bid[1])
                    })
                for ask in data.get("asks", []):
                    order_book["asks"].append({
                        "price": str(ask[0]),
                        "quantity": str(ask[1])
                    })
            return order_book
        except Exception as e:
            raise ValueError(str(e))

    def get_current_price(self, symbol):
        try:
            if self.account_type == "F":
                return self.get_future_exchange_price(symbol)
            endpoint = "/api/v3/ticker/price"
            params = {
                "symbol": symbol
            }
            response = self._send_request('GET', endpoint, params)
            # print(response)
            if isinstance(response, dict) and response.get("price"):
                return str(response.get("price"))
            raise ValueError("Price not found in response")
        except Exception as e:
            raise ValueError(str(e))
        
    def get_future_exchange_price(self, symbol):
        try:
            endpoint = "/api/v1/contract/ticker"
            params = {
                "symbol": symbol
            }
            response = self._send_futures_request('GET', endpoint, params)
            # print(response)
            if isinstance(response, dict) and response.get("data") and response.get("data").get("lastPrice"):
                return str(response.get("data").get("lastPrice"))
            raise ValueError("Price not found in response")
        except Exception as e:
            raise ValueError(str(e))
        
    