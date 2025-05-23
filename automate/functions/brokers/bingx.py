import time
import requests
import json

from .broker import CryptoBrokerClient
from .types import *

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


    def send_request(self, method, path, payload, data={}):
        paramsMap = {
            **payload,
            "recvWindow": "60000",
            "timestamp": self._get_timestamp(),
        }
        paramsStr = self.parseParam(paramsMap)

        url = "%s%s?%s&signature=%s" % (self.BASE_URL, path, paramsStr, self.create_signature(paramsStr))
        # print(url)
        headers = {
            'X-BX-APIKEY': self.api_key,
        }
        response = requests.request(method, url, headers=headers, data=data)
        return response.json()

    def parseParam(self, paramsMap):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        if paramsStr != "": 
            return paramsStr+"&timestamp="+str(int(time.time() * 1000))
        else:
            return paramsStr+"timestamp="+str(int(time.time() * 1000))

    
    def get_account_info(self):
        payload = {}

        if self.account_type == 'S':
            path = '/openApi/spot/v1/account/balance'
        else:
            path = '/openApi/swap/v3/user/balance'

        respons =  self.send_request("GET", path, payload)


        # print("Response:", respons)
        if respons:
            try:
                data = respons
                if data.get('code') == 0:
                    return data.get('data')
                else:
                    print("Error:", data.get('msg'))
                    return None
            except json.JSONDecodeError as e:
                print("JSON Decode Error:", e)
                return None
        else:
            print("No response from server")
            return None
        

    def get_account_balance(self) -> AccountBalance:
        try:
            account_info = self.get_account_info()
            
            balances = {}
            # Expected structure:
            # {"code":200, "data": {"balances": [{"asset": "BTC", "free": "0.1", ...}, ...]}}
            if self.account_type == 'S':
                for balance in account_info["balances"]:
                    balances[balance["asset"]] = {
                        "available": float(balance["free"]),
                        "locked": float(balance["locked"])
                    }
            else:
                for balance in account_info:
                    balances[balance["asset"]] = {
                        "available": float(balance["balance"]),
                        "locked": float(balance["unrealizedProfit"])
                    }
                
            return balances
        except Exception as e:
            raise ValueError(str(e))
        
    
    def get_exchange_info(self, symbol) -> ExchangeInfo:
        params = {
            "symbol": symbol
        }
  
        endpoint = '/openApi/spot/v1/common/symbols'

        if self.account_type == 'U':
            endpoint = '/openApi/swap/v2/quote/contracts'
        elif self.account_type == 'C':
            endpoint = '/openApi/cswap/v1/market/contracts'

        response = self.send_request('GET', endpoint, params)
        response_data = response.get("data")

        print("Symbols:", response_data, self.account_type)

        if self.account_type == 'S':
            if isinstance(response_data, dict) and response_data.get("symbols"):
                symbols = response_data.get("symbols")
                for s in symbols:
                    if s.get("symbol") == symbol:
                        symbol = s.get("symbol")
                        base_asset, quote_asset = symbol.split("-")

                        min_qty = s.get("minQty")
                        min_value = s.get("minNotional")

                        base_decimals = self.get_decimals_from_step(min_qty)
                        quote_decimals = self.get_decimals_from_step(min_value)
                        
                        return {
                            "symbol": symbol,
                            "base_asset": base_asset,
                            "quote_asset": quote_asset,
                            "base_decimals": base_decimals,
                            "quote_decimals": quote_decimals,
                        }
        elif self.account_type == 'U':
            if isinstance(response_data, list):
                symbols = response_data
                for s in symbols:
                    if s.get("symbol") == symbol:
                        symbol = s.get("symbol")
                        base_asset = s.get("asset")
                        quote_asset = s.get("currency")

                        min_qty = s.get("quantityPrecision")
                        min_value = s.get("minNotional")

                        base_decimals = s.get("quantityPrecision")
                        quote_decimals = s.get("pricePrecision")
                        
                        return {
                            "symbol": symbol,
                            "base_asset": base_asset,
                            "quote_asset": quote_asset,
                            "base_decimals": base_decimals,
                            "quote_decimals": quote_decimals,
                        }
            
        raise ValueError("Symbol not found")
    

    def open_trade(self, symbol: str, side: str, quantity: float, oc = False, custom_id: str = None) -> OpenTrade:
        try:
            endpoint = '/openApi/spot/v1/trade/order'
            if self.account_type == 'U':
                endpoint = '/openApi/swap/v2/trade/order'
            elif self.account_type == 'C':
                endpoint = '/openApi/cswap/v1/trade/order'
            
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
            if oc:
                order_params["reduceOnly"] = True
            if self.account_type != 'S':
                order_params["positionSide"] = "LONG" if side.upper() == "BUY" else "SHORT"

            response = self.send_request('POST', endpoint, order_params)

            print("Response:", response)
            if response.get("code") != 0:
                raise ValueError(f"{response.get('msg')}")
            
            order_data = response.get("data")

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
                endpoint = '/openApi/cswap/v1/trade/orderDetail'

            response_data = self.send_request('GET', endpoint, params)
            
            if isinstance(response_data, dict) and response_data.get("code") == 0:
                trade = response_data.get("data")

                if self.account_type == 'S':
                    fees = float(trade.get('fee'))
                    fees = self.calculate_fees(symbol, trade.get('price', '0'), fees, trade.get('feeAsset'))
                else:
                    fees = trade.get('commission')

                return {
                    "symbol": trade.get("symbol"),
                    "order_id": str(trade.get("orderId")),
                    "volume": trade.get("executedQty"),
                    "side": trade.get("side"),
                    "time": self.convert_timestamp(trade.get("time")),
                    "price": trade.get("price"),
                    "fees": str(fees),
                    "profit": trade.get("profit", None),
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
                raise ValueError("Order not found")
        except Exception as e:
            raise ValueError(str(e))


