import time
import requests
import json

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

class BingxClient(CryptoBrokerClient):
    BASE_URL = 'https://open-api.bingx.com'

    @staticmethod
    def check_credentials(api_key, secret_key, account_type):
        try:
            client = BingxClient(api_key=api_key, api_secret=secret_key, account_type=account_type)
            account = client.get_account_info()
            if not account:  # Example error code handling
                return {'error': "Invalid API key or secret.", "valid": False}
            return {'message': "API credentials are valid.", "valid": True}
        except Exception as e:
            return {'error': str(e), "valid": False}


    def _send_request(self, method, path, payload, data={}):
        paramsMap = {
            **payload,
            "recvWindow": "60000",
            "timestamp": self._get_timestamp(),
        }
        paramsStr = self._parseParam(paramsMap)

        url = "%s%s?%s&signature=%s" % (self.BASE_URL, path, paramsStr, self._create_signature(paramsStr))
        # print(url)
        headers = {
            'X-BX-APIKEY': self.api_key,
        }
        response = requests.request(method, url, headers=headers, data=data)
        return response.json()

    def _parseParam(self, paramsMap):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        if paramsStr != "": 
            return paramsStr+"&timestamp="+str(int(time.time() * 1000))
        else:
            return paramsStr+"timestamp="+str(int(time.time() * 1000))

    
    def get_account_info(self):
        payload = {}

        path = '/openApi/spot/v1/account/balance'
        
        if self.account_type == 'U':
            path = '/openApi/swap/v3/user/balance'
        elif self.account_type == 'C':
            path = '/openApi/cswap/v1/user/balance'

        respons =  self._send_request("GET", path, payload)


        # print("Response:", respons)
        if respons:
            try:
                data = respons
                if data.get('code') == 0:
                    return data.get('data')
                else:
                    print("Error:", data.get('msg'))
                    raise Exception(data.get('msg'))
            except json.JSONDecodeError as e:
                print("JSON Decode Error:", e)
                return None
        else:
            print("No response from server")
            raise Exception("No response from server")
        

    def get_account_balance(self, symbol:str = None) -> AccountBalance:
        try:
            account_info = self.get_account_info()
            
            balances = {}
            # Expected structure:
            # {"code":200, "data": {"balances": [{"asset": "BTC", "free": "0.1", ...}, ...]}}
            if self.account_type == 'S':
                for balance in account_info["balances"]:
                    if symbol and balance["asset"] not in symbol:
                        continue
                    balances[balance["asset"]] = {
                        "available": float(balance["free"]),
                        "locked": float(balance["locked"])
                    }
            else:
                for balance in account_info:
                    if symbol and balance["asset"] not in symbol:
                        continue
                    balances[balance["asset"]] = {
                        "available": float(balance["balance"]),
                        "locked": float(balance["unrealizedProfit"])
                    }
                
            return balances
        except Exception as e:
            raise ValueError(str(e))
        
    
    def get_exchange_info(self, symbol) -> ExchangeInfo:
        symbol = self.adjust_symbol_name(symbol)
        params = {
            "symbol": symbol
        }
  
        endpoint = '/openApi/spot/v1/common/symbols'

        if self.account_type == 'U':
            endpoint = '/openApi/swap/v2/quote/contracts'
        elif self.account_type == 'C':
            endpoint = '/openApi/cswap/v1/market/contracts'

        response = self._send_request('GET', endpoint, params)
        response_data = response.get("data")

        if self.account_type == 'S':
            if isinstance(response_data, dict) and response_data.get("symbols"):
                symbols = response_data.get("symbols")
                for s in symbols:
                    if s.get("symbol") == symbol:
                        symbol = s.get("symbol")
                        base_asset, quote_asset = symbol.split("-")


                        base_decimals = self.get_decimals_from_step(s.get("stepSize"))
                        quote_decimals = self.get_decimals_from_step(s.get("tickSize"))
                        
                        return {
                            "symbol": symbol,
                            "base_asset": base_asset,
                            "quote_asset": quote_asset,
                            "base_decimals": base_decimals,
                            "quote_decimals": quote_decimals,
                            "min_qty": s.get("minQty", None),
                            "min_value": s.get("minNotional", None),
                            "max_qty": s.get("maxQty", None),
                            "max_value": s.get("maxNotional", None),
                        }
        elif self.account_type == 'U':
            if isinstance(response_data, list):
                symbols = response_data
                for s in symbols:
                    if s.get("symbol") == symbol:
                        symbol = s.get("symbol")
                        base_asset = s.get("asset")
                        quote_asset = s.get("currency")

                        base_decimals = s.get("quantityPrecision")
                        quote_decimals = s.get("pricePrecision")
                        
                        return {
                            "symbol": symbol,
                            "base_asset": base_asset,
                            "quote_asset": quote_asset,
                            "base_decimals": base_decimals,
                            "quote_decimals": quote_decimals,
                            "min_qty": s.get("tradeMinQuantity", None),
                            "min_value": s.get("tradeMinUSDT", None),
                        }
                    
        elif self.account_type == 'C':
            if isinstance(response_data, list):
                symbols = response_data
                for s in symbols:
                    if s.get("symbol") == symbol:
                        symbol = s.get("symbol")
                        base_asset, quote_asset = symbol.split("-")

                        min_qty = s.get("minQty")
                        min_value = s.get("minTradeValue")
                        
                        return {
                            "symbol": symbol,
                            "base_asset": base_asset,
                            "quote_asset": quote_asset,
                            "base_decimals": s.get("pricePrecision"),
                            "quote_decimals": s.get("pricePrecision"),
                            'min_qty': min_qty,
                            'min_value': min_value,
                        }
            
        raise ValueError("Symbol not found")
    

    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None, oc = False) -> OpenTrade:
        try:
            endpoint = '/openApi/spot/v1/trade/order'
            if self.account_type == 'U':
                endpoint = '/openApi/swap/v2/trade/order'
            elif self.account_type == 'C':
                endpoint = '/openApi/cswap/v1/trade/order'
            
            sys_info = self.get_exchange_info(symbol)
            
            base_asset = sys_info.get('base_asset')
            order_symbol = sys_info.get('symbol')
            currency_asset = sys_info.get('quote_asset')

            # data = self.get_order_info(symbol, '1926362720564678657')
            # raise Exception(data)

            if self.account_type == 'C':
                currency_asset = base_asset

            adjusted_quantity = self.adjust_trade_quantity(sys_info, side, float(quantity))
            # adjusted_quantity = quantity
            print("Adjusted quantity:", adjusted_quantity)

            
            order_params = {
                "symbol": order_symbol,
                "side": side.upper(),
                "type": "MARKET",  # Using lowercase as per MEXC docs
                "quantity": adjusted_quantity,
            }

            if self.account_type != 'S':
                if oc:
                    order_params["positionSide"] = "LONG" if side.upper() == "SELL" else "SHORT"
                else:
                    order_params["positionSide"] = "LONG" if side.upper() == "BUY" else "SHORT"
                # order_params["reduceOnly"] = True
                # order_params["type"] = 'STOP_MARKET'
                pass

            print(order_params)

            response = self._send_request('POST', endpoint, order_params)

            print("Response:", response)
            if response.get("code") is not None:
                if response.get("code") != 0:
                    error_msg = response.get('msg')
                    if error_msg in ('', None):
                        error_msg = 'an error occured! #' + str(response.get("code"))

                    raise ValueError(error_msg)
                order_data = response.get("data")
            else:
                order_data = response
            
            order_id = order_data.get('orderId')

            if not order_id:
                order_id = order_data.get('order', {}).get('orderId')

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
                    'currency': order_details.get('currency') if order_details.get('currency') is not None else currency_asset,

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
                    'time': self.convert_timestamp(order_data.get('transactTime', '')),
                    'qty': adjusted_quantity,
                    'currency': currency_asset,
                }
        except Exception as e:
            raise ValueError(str(e))
            

    def close_trade(self, symbol: str, side: str, quantity: float) -> CloseTrade:
        try:
            t_side = "SELL" if side.upper() == "BUY" else "BUY"
            return self.open_trade(symbol, t_side, quantity, oc=True)
        except Exception as e:
            raise ValueError(str(e))


    def get_order_info(self, symbol: str, order_id: str) -> OrderInfo:
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id
            }
            endpoint = '/openApi/spot/v1/trade/query'
            if self.account_type == 'U':
                endpoint = '/openApi/swap/v2/trade/order'
            elif self.account_type == 'C':
                endpoint = '/openApi/cswap/v1/trade/allFillOrders'
                time.sleep(2)

            response_data = self._send_request('GET', endpoint, params)
            
            if isinstance(response_data, dict) and response_data.get("code") == 0:
                trade = response_data.get("data")

                if self.account_type == 'U':
                    trade = trade.get('order')
                elif self.account_type == 'C':
                    if trade and len(trade) > 0:
                        trade = trade[0]
                    else:
                        raise Exception('Order not found')

                # print(trade)

                if self.account_type == 'S':
                    fees = float(trade.get('fee'))
                    fees = self.calculate_fees(symbol, trade.get('price', '0'), fees, trade.get('feeAsset'))
                else:
                    fees = trade.get('commission')
                    fees = self.calculate_fees(symbol, 0, fees=fees)
                    
                if self.account_type == 'C':
                    return {
                        "symbol": trade.get("symbol"),
                        "order_id": str(trade.get("orderId")),
                        "volume": trade.get('volume'),
                        "side": trade.get("side"),
                        "time": self.convert_timestamp(trade.get("tradeTime")),
                        "price": trade.get("tradePrice"),
                        "fees": str(fees),
                        "profit": trade.get("realizedPnl"),
                        "currency": trade.get('currency'),
                    }

                return {
                    "symbol": trade.get("symbol"),
                    "order_id": str(trade.get("orderId")),
                    "volume": trade.get("executedQty"),
                    "side": trade.get("side"),
                    "time": self.convert_timestamp(trade.get("time")),
                    "price": trade.get("price") if trade.get("price") not in [None, "0", 0] else trade.get("avgPrice"),
                    "fees": str(fees),
                    "profit": trade.get("profit") if trade.get("profit") not in [None, "0", 0] else trade.get("realizedPnl"),
                    "currency": trade.get('currency'),
                    "additional_info": {
                        "status": trade.get("status"),
                        "avg_price": trade.get("avgFillPrice"),
                        "client_order_id": trade.get("clientOrderId"),
                        "cummulative_quote_qty": trade.get("cummulativeQuoteQty"),
                        "fee": trade.get("fee"),
                        "fee_asset": trade.get("feeAsset"),
                    }
                }
            else:
                raise ValueError(f"Order not found")
        except Exception as e:
            print(f'error getting order {order_id} info ', e)
            return None

    
    def get_current_price(self, symbol):
        try:
            params = {
                "symbol": symbol
            }
            endpoint = '/openApi/spot/v1/ticker/price'
            if self.account_type == 'U':
                endpoint = '/openApi/swap/v2/quote/ticker'
            elif self.account_type == 'C':
                endpoint = '/openApi/cswap/v1/market/ticker'

            response_data = self._send_request('GET', endpoint, params)
            # print("Price response:", response_data)

            if isinstance(response_data, dict) and response_data.get("code") == 0:
                trade = response_data.get("data")

                if isinstance(trade, list) and len(trade) > 0:
                    trade = trade[0]

                t = trade.get('trades', {})

                if t and isinstance(t, list) and len(t) > 0:
                    trade = t[0]

                # print("Trade data:", trade)
                if self.account_type in ['U', 'C']:
                    return float(trade.get('lastPrice'))
                
                

                return float(trade.get('price'))
            else:
                raise Exception(response_data.get("msg", "Could not fetch price"))
        except Exception as e:
            raise ValueError(str(e))
        
    def get_trading_pairs(self):
        try:
            endpoint = '/openApi/spot/v1/common/symbols'
            if self.account_type == 'U':
                endpoint = '/openApi/swap/v2/quote/contracts'
            elif self.account_type == 'C':
                endpoint = '/openApi/cswap/v1/market/contracts'

            response_data = self._send_request('GET', endpoint, {})
            # print("Pairs response:", response_data)

            pairs = []
            if isinstance(response_data, dict) and response_data.get("code") == 0:
                data = response_data.get("data")
                if self.account_type == 'S':
                    symbols = data.get("symbols")
                    for s in symbols:
                        pairs.append(s.get("symbol"))
                else:
                    symbols = data
                    for s in symbols:
                        pairs.append(s.get("symbol"))
                return pairs
            else:
                raise Exception(response_data.get("msg", "Could not fetch trading pairs"))
        except Exception as e:
            raise ValueError(str(e))
        
    def get_history_candles(self, symbol, interval, limit = 500):
        try:
            if limit> 1440:
                limit = 1440
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            endpoint = '/openApi/spot/v2/market/kline'
            if self.account_type == 'U':
                endpoint = '/openApi/swap/v3/quote/klines'
            elif self.account_type == 'C':
                endpoint = '/openApi/cswap/v1/market/klines'

            response_data = self._send_request('GET', endpoint, params)

            candles = []
            if isinstance(response_data, dict) and response_data.get("code") == 0:
                # print("Candles response:", response_data) 
                data = response_data.get("data")
                for c in data:
                    if self.account_type == 'S':
                        candles.append({
                            'timestamp': self.convert_timestamp(c[0]),
                            'open': float(c[1]),
                            'high': float(c[2]),
                            'low': float(c[3]),
                            'close': float(c[4]),
                            'volume': float(c[5]),
                        })
                    elif self.account_type in ['U', 'C']:
                        candles.append({
                            'timestamp': self.convert_timestamp(c.get('time')),
                            'open': float(c.get('open')),
                            'high': float(c.get('high')),
                            'low': float(c.get('low')),
                            'close': float(c.get('close')),
                            'volume': float(c.get('volume')),
                        })
                return candles
            else:
                raise Exception(response_data.get("msg", "Could not fetch candles"))
        except Exception as e:
            raise ValueError(str(e))
        
    def get_order_book(self, symbol, limit=10):
        try:
            if self.account_type == 'S':
                if limit < 20:
                    limit = 20
                elif limit > 1000:
                    limit = 1000
            elif self.account_type in ['U', 'C']:
                if limit not in [5, 10, 20, 50, 100, 500, 1000]:
                    limit = 100

            params = {
                "symbol": symbol,
                "limit": limit
            }
            endpoint = '/openApi/spot/v1/market/depth'
            if self.account_type == 'U':
                endpoint = '/openApi/swap/v2/quote/depth'
            elif self.account_type == 'C':
                endpoint = '/openApi/cswap/v1/market/depth'

            response_data = self._send_request('GET', endpoint, params)
            # print("Order Book response:", response_data)

            if isinstance(response_data, dict) and response_data.get("code") == 0:
                data = response_data.get("data")
                return {
                    'bids': [{"price":float(price), "qty":float(quantity)} for price, quantity in data.get('bids', [])],
                    'asks': [{"price":float(price), "qty":float(quantity)} for price, quantity in data.get('asks', [])],
                }
            else:
                raise Exception(response_data.get("msg", "Could not fetch order book"))
        except Exception as e:
            raise ValueError(str(e))