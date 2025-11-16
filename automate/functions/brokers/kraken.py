# Spot: Quantity is in base asset units. Account balance needs to have enough base and quote asset to trade in both directions.
# Futures: Available for certain account types. Doesn't include expiry and stocks (Not tested yet)


import time
import http.client
import urllib.request
import urllib.parse
import hashlib
import hmac
import base64
import json

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

class KrakenClient(CryptoBrokerClient):
    symbol_cache = {}

    def __init__(self, account=None, api_key=None, api_secret=None, account_type="S", current_trade=None):
        super().__init__(account=account, api_key=api_key, api_secret=api_secret, account_type=account_type, current_trade=current_trade)
        self.base_url = "https://api.kraken.com"
        if self.account_type.upper() == "F":
            self.base_url = "https://futures.kraken.com"

    def _get_signature(self, data: str, nonce: str, path: str) -> str:
        message = path.encode() + hashlib.sha256((nonce + data).encode()).digest() 
        if self.account_type == "F":
            message = hashlib.sha256((data + nonce + path.removeprefix("/derivatives")).encode()).digest()
        return self._sign(message=message)

    def _sign(self, message: bytes) -> str:
        sign = base64.b64encode(
            hmac.new(
                key=base64.b64decode(self.api_secret),
                msg=message,
                digestmod=hashlib.sha512,
            ).digest())
        
        if self.account_type == "F":
            return sign.decode()
        else:
            return sign


    def _request(self, method: str = "GET", path: str = "", query: dict | None = None, body: dict | None = None) -> http.client.HTTPResponse:
        url = self.base_url + path
        query_str = ""
        if query is not None and len(query) > 0:
            query_str = urllib.parse.urlencode(query)
            url += "?" + query_str
        nonce = ""
        body_str = ""
        headers = {}
        if self.account_type == "S":
            if len(self.api_key) > 0:
                if body is None:
                    body = {}
                nonce = body.get("nonce")
                if nonce is None:
                    nonce = str(self._get_timestamp())
                    body["nonce"] = nonce        
            if body is not None and len(body) > 0:
                body_str = json.dumps(body)
                headers["Content-Type"] = "application/json"
        if self.account_type == "F":
            if body is not None and len(body) > 0:
                body_str = urllib.parse.urlencode(body)
                

        if len(self.api_secret) > 0:
            if self.account_type.upper() == "F":
                headers["APIKey"] = self.api_key 
                nonce =  "" #str(self._get_timestamp())
                headers["Authent"] = self._get_signature(query_str+body_str, nonce, path)
                if len(nonce) > 0:
                    headers["Nonce"] = nonce
            else:
                headers["API-Key"] = self.api_key
                headers["API-Sign"] = self._get_signature(query_str+body_str, nonce, path)

        req = urllib.request.Request(
            method=method,
            url=url,
            data=body_str.encode(),
            headers=headers,
        )
        return urllib.request.urlopen(req)
    
    @staticmethod
    def check_credentials(api_key: str, api_secret: str, account_type="S"):
        try:
            client = KrakenClient(api_key=api_key, api_secret=api_secret, account_type=account_type)
            account = client.get_account_balance()
            # print(account)
            if not account:
                raise Exception("API credentials are invalid.")
            return {'message': "API credentials are valid.", "valid": True}
        except Exception as e:
            return {'error': str(e), "valid": False}
        
    def get_current_price(self, symbol):
        try:
            symbol = self.adjust_symbol_name(symbol)
            if self.account_type == "F":
                response = self._request(
                    method="GET",
                    path="/derivatives/api/v3/tickers/"+symbol,
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching exchange info: " + str(data["error"]))
                result = data.get("ticker", {})
                return float(result.get("bid", 0.0))
            
            else:
                response = self._request(
                    method="GET",
                    path="/0/public/Ticker",
                    query={"pair": symbol},
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching exchange info: " + str(data["error"]))
                result = data.get("result", {})
                if symbol in result:
                    return float(result[symbol]["c"][0])
                raise Exception("Symbol not found: " + symbol)
        except Exception as e:
            raise e
        
    def get_exchange_info(self, symbol):
        try:
            symbol = self.adjust_symbol_name(symbol)
            if symbol in self.symbol_cache:
                return self.symbol_cache[symbol]
            if self.account_type == "F":
                response = self._request(
                    method="GET",
                    path="/derivatives/api/v3/instruments",
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching exchange info: " + str(data["error"]))
                result = data.get("instruments", [])
                for item in result:
                    if item.get("symbol") == symbol:
                        sym = {
                            "symbol": item["symbol"],
                            "pair": item["pair"],
                            "base_asset": item["base"],
                            "quote_asset": item["quote"],
                            "base_decimals": self.get_decimals_from_step(item["tickSize"]),
                            "quote_decimals": item['contractValueTradePrecision'],
                            "contract_val": float(item.get("contractSize", 1.0)),
                        }
                        self.symbol_cache[symbol] = sym
                        return sym
            else:
                symbol = self.adjust_symbol_name(symbol)
                response = self._request(
                    method="GET",
                    path="/0/public/AssetPairs",
                    query={ "pair": symbol },
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching exchange info: " + str(data["error"]))
                result = data.get("result", {})
                if symbol in result:
                    symb_info = result[symbol]
                    sym = {
                        "symbol": symb_info["altname"],
                        "base_asset": symb_info["base"],
                        "quote_asset": symb_info["quote"],
                        "base_decimals": symb_info['pair_decimals'],
                        "quote_decimals": symb_info['lot_decimals'],
                        "min_order_size": float(symb_info["ordermin"]),
                    }
                    self.symbol_cache[symbol] = sym
                    return sym
            raise Exception("Symbol not found: " + symbol)
        except Exception as e:
            raise e
        
    def get_account_balance(self, symbol = None):
        try:
            if self.account_type.upper() == "F":
                response = self._request(
                    method="GET",
                    path="/derivatives/api/v3/accounts",
                )
                data = json.loads(response.read())
                print("Account balance data:", data)
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching account: " + str(data["error"]))
                result = data.get("balances", {})

                balances = {}
                for item in result:
                    asset = item.get("currency")
                    available = float(item.get("availableBalance", 0.0))
                    locked = float(item.get("openOrderReserve", 0.0))
                    if symbol and asset not in symbol:
                        continue
                    # print(f"Asset: {asset}, Available: {available}, Locked: {locked}")
                    balances[asset] = {"available": available, "locked": locked}
                    
                return balances


            else:
                response = self._request(
                    method="POST",
                    path="/0/private/Balance",
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching account: " + str(data["error"]))
                result = data.get("result", {})

                balances = {}
                for k, v in result.items():
                    if symbol and k not in symbol:
                        continue
                    # print(f"Asset: {k}, Balance: {v}")
                    balances[k] = {"available": float(v), "locked": 0.0}
                    
                return balances
        except Exception as e:
            raise e

    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None, oc:bool = False) -> OpenTrade:
        try:
            symbol_info = self.get_exchange_info(symbol)

            if not symbol_info:
                raise Exception('Symbol was not found!')
            
            print("Symbol info:", symbol_info)

            adjusted_quantity = self.adjust_trade_quantity(symbol_info, side, quantity)

            quote_asset = symbol_info.get('quote_asset')
            order_symbol = symbol_info.get('symbol')
            pair = symbol_info.get('pair', order_symbol)

            order_type = "buy" if side.lower() == "buy" else "sell"

            if self.account_type == "F":
                body = {
                    "symbol": order_symbol,
                    "side": order_type.upper(),
                    "orderType": "mkt",
                    "size": adjusted_quantity,
                }
                if oc:
                    body["reduceOnly"] = True

                response = self._request(
                    method="POST",
                    path="/derivatives/api/v3/sendorder",
                    body=body,
                )
                end_exe = time.perf_counter()
                data = json.loads(response.read())

                print("Open trade response data:", data)

                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error opening trade: " + str(data["error"]))
                result = data.get("sendStatus", {})
                order_id = result.get("order_id", None)
            
            elif self.account_type == "S":
                body = {
                        "ordertype": "market",
                        "type": order_type,
                        "pair": order_symbol,
                        "volume": str(adjusted_quantity),
                        # "timeinforce": "IOC",
                    }
                
                print("Open trade body:", body)

                response = self._request(
                    method="POST",
                    path="/0/private/AddOrder",
                    body=body,
                )
                end_exe = time.perf_counter()
                data = json.loads(response.read())

                print("Open trade response data:", data)

                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error opening trade: " + str(data["error"]))
                result = data.get("result", {})
                order_id = result.get("txid", [None])[0]
            else:
                raise Exception("Unsupported account type for opening trades: " + self.account_type)
            

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
                    'symbol': symbol,
                    "side": side.upper(),
                    'qty': order_details.get('volume', adjusted_quantity),
                    'price': order_details.get('price', '0'),
                    'time': order_details.get('time', ''),
                    'fees': order_details.get('fees', ''),
                    'currency': quote_asset,

                    'trade_details': trade_details,
                    "end_exe": end_exe
                }
            else:
                raise Exception("Failed to retrieve order details after opening trade.")
        except Exception as e:
            raise e

    def close_trade(self, symbol: str, side: str, quantity: float) -> CloseTrade:
        t_side = "SELL" if side.upper() in ("BUY", "B") else "BUY"
        return self.open_trade(symbol, t_side, quantity, oc=True)

    def get_order_info(self, symbol, order_id):
        try:
            # print("Fetching order info for order ID:", order_id)
            account_type = self.account_type
            self.account_type = "S"
            response = self._request(
                method="POST",
                path="/0/private/TradesHistory",
                body={
                    "start": order_id,
                    "end": order_id,
                },
            )
            self.account_type = account_type

            data = json.loads(response.read())
            if "error" in data and len(data["error"]) > 0:
                raise Exception("Error fetching order info: " + str(data["error"]))
            result = data.get("result", {})
            trades = result.get("trades", {})
            for trade_id, trade_info in trades.items():
                if trade_info.get("ordertxid") == order_id:
                    return {
                        "symbol": trade_info.get("pair"),
                        "order_id": order_id,
                        "volume": float(trade_info.get("vol")),
                        "price": float(trade_info.get("price")),
                        "side": "buy" if trade_info.get("type") == "buy" else "sell",
                        "time": self.convert_timestamp(int(float(trade_info.get("time"))) * 1000),
                        "fees": float(trade_info.get("fee")),
                    }
            raise Exception("Order ID not found: " + order_id) 

        except Exception as e:
            raise e
    
    def get_trading_pairs(self):
        try:
            if self.account_type == "F":
                response = self._request(
                    method="GET",
                    path="/derivatives/api/v3/tickers"
                )
                data = json.loads(response.read())

                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching trading pairs: " + str(data["error"]))
                symbols = [s.get('symbol') for s in data.get('tickers', [])]

                return symbols

            else:
                response = self._request(
                    method="GET",
                    path="/0/public/AssetPairs",
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching trading pairs: " + str(data["error"]))
                result = data.get("result", {})
                return list(result.keys())
        except Exception as e:
            print("Error in get_trading_pairs:", e)
            return []
    
    def get_history_candles(self, symbol, interval:str , limit = 500):
        try:
            symbol = self.adjust_symbol_name(symbol)
            if self.account_type == "F":
                possible_intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
                if interval not in possible_intervals:
                    raise Exception("Invalid interval for futures: " + interval)
                response = self._request(
                    method="GET",
                    path="/api/charts/v1/mark/"+symbol+"/"+interval,
                    query={
                        "count": limit,
                    },
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching historical candles: " + str(data["error"]))
                result = data.get("candles", [])
                return [
                    {
                        "time": self.convert_timestamp(int(c['time'])),
                        "open": float(c['open']),
                        "high": float(c['high']),
                        "low": float(c['low']),
                        "close": float(c['close']),
                        "volume": float(c['volume']),
                    }
                    for c in result
                ]
            
            else:
                mins_interval = 1

                if "m" in interval:
                    mins_interval = int(interval.replace("m", ""))
                elif "h" in interval:
                    mins_interval = int(interval.replace("h", "")) * 60
                elif "d" in interval:
                    mins_interval = int(interval.replace("d", "")) * 60 * 24
                elif "w" in interval:
                    mins_interval = int(interval.replace("w", "")) * 60 * 24 * 7
                elif "M" in interval:
                    mins_interval = int(interval.replace("M", "")) * 60 * 24 * 30

                response = self._request(
                    method="GET",
                    path="/0/public/OHLC",
                    query={
                        "pair": symbol,
                        "interval": mins_interval,
                        "since": int(time.time()) - limit * mins_interval * 60,
                    },
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching historical candles: " + str(data["error"]))
                result = data.get("result", {})
                if symbol in result:
                    candles = result[symbol]
                    return [
                        {
                            "time": self.convert_timestamp(int(c[0]) * 1000),
                            "open": float(c[1]),
                            "high": float(c[2]),
                            "low": float(c[3]),
                            "close": float(c[4]),
                            "volume": float(c[6]),
                        }
                        for c in candles
                    ]
            raise Exception("Symbol not found: " + symbol)
        except Exception as e:
            print("Error in get_history_candles:", e)
            return []

    def get_order_book(self, symbol, limit = 100):
        try:
            symbol = self.adjust_symbol_name(symbol)
            if self.account_type == "F":
                response = self._request(
                    method="GET",
                    path="/derivatives/api/v3/orderbook",
                    query={
                        "symbol": symbol,
                    },
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching order book: " + str(data["error"]))
                result = data.get("orderBook", {})
                return {
                    "bids": [
                        {"price": float(bid[0]), "qty": float(bid[1])}
                        for bid in result.get("bids", [])
                    ],
                    "asks": [
                        {"price": float(ask[0]), "qty": float(ask[1])}
                        for ask in result.get("asks", [])
                    ],
                }
            else:
                response = self._request(
                    method="GET",
                    path="/0/public/Depth",
                    query={
                        "pair": symbol,
                        "count": limit,
                    },
                )
                data = json.loads(response.read())
                if "error" in data and len(data["error"]) > 0:
                    raise Exception("Error fetching order book: " + str(data["error"]))
                result = data.get("result", {})
                if symbol in result:
                    order_book = result[symbol]
                    return {
                        "bids": [
                            {"price": float(bid[0]), "qty": float(bid[1]), "time": self.convert_timestamp(int(bid[2]) * 1000)}
                            for bid in order_book.get("bids", [])
                        ],
                        "asks": [
                            {"price": float(ask[0]), "qty": float(ask[1]), "time": self.convert_timestamp(int(ask[2]) * 1000)}
                            for ask in order_book.get("asks", [])
                        ],
                    }
            raise Exception("Symbol not found: " + symbol)
        except Exception as e:
            print("Error in get_order_book:", e)
            return {"bids": [], "asks": []}