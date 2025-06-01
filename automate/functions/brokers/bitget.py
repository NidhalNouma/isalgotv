import time
import hmac
import hashlib
import requests
import base64
import json

from decimal import Decimal

from .types import *
from .broker import CryptoBrokerClient

class BitgetClient(CryptoBrokerClient):

    BITGET_API_URL = 'https://api.bitget.com'

    @staticmethod
    def check_credentials(api_key, api_secret, phrase, account_type="S"):
        """
        Static method to validate Bitget API credentials without instantiation.
        """
        try:
            endpoint = '/api/v2/spot/account/info'
            if account_type == "U":
                endpoint = '/api/v2/mix/account/accounts?productType=USDT-FUTURES'
            elif account_type == "C":
                endpoint = '/api/v2/mix/account/accounts?productType=COIN-FUTURES'
            elif account_type == "US":
                endpoint = '/api/v2/mix/account/accounts?productType=USDC-FUTURES'

            client = BitgetClient(api_key=api_key, api_secret=api_secret, passphrase=phrase,account_type=account_type)

            response = client.send_request('GET', endpoint)
            # Adjust these checks to match Bitget’s actual response format:
            if response.get('code') != '00000':
                return {'error': response.get('msg'), 'valid': False}
            return {'message': "API credentials are valid.", 'valid': True}
        except Exception as e:
            return {'error': str(e), 'valid': False}

    def create_signature(self, timestamp, method, request_path, body=''):
        if isinstance(body, dict):
            body = json.dumps(body)

        message = timestamp + method.upper() + request_path + body
        return base64.b64encode(hmac.new(self.api_secret.encode(), message.encode(), hashlib.sha256).digest()).decode()

    def send_request(self, method, endpoint, body=None):
        timestamp = str(int(time.time() * 1000))

        headers = {
            'ACCESS-KEY': self.api_key,
            'ACCESS-SIGN': self.create_signature(timestamp, method, endpoint, body or ''),
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }

        url = f"{self.BITGET_API_URL}{endpoint}"
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers, json=body)
        return response.json()

    def get_exchange_info(self, symbol) -> ExchangeInfo:
        """
        Retrieve symbol precision and asset info from Bitget.
        """
        endpoint = f"/api/v2/spot/public/symbols?symbol={symbol}"

        try:
            if self.account_type == "U":
                productType = "USDT-FUTURES"
                endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
            elif self.account_type == "C":
                productType = "COIN-FUTURES"
                endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
            elif self.account_type == "UC":
                productType = "USDC-FUTURES"
                endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"

            response = self.send_request('GET', endpoint)
            # print(response )

            if not response.get('data'):
                raise Exception('Symbol does not exist')

            data = response['data'][0]
            
            return {
                'symbol': data.get('symbol'),
                'base_asset': data.get('baseCoin'),
                'quote_asset': data.get('quoteCoin'),
                'base_decimals': data.get('quantityPrecision') or data.get('volumePlace'),
                'quote_decimals':  data.get('quotePrecision') or data.get('pricePlace'),
            }
        except Exception as e:
            raise Exception(e)
        

    def get_exchange_price(self, symbol):
        # Endpoint for placing an order
        endpoint = f"/api/v2/spot/market/tickers?symbol={symbol}"

        if self.account_type == "U":
            productType = "USDT-FUTURES"
            endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
        elif self.account_type == "C":
            productType = "COIN-FUTURES"
            endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
        elif self.account_type == "UC":
            productType = "USDC-FUTURES"
            endpoint = f"/api/v2/mix/market/contracts?symbol={symbol}&productType={productType}"
    
        response = self.send_request('GET', endpoint)
        data = response['data'][0]
        if data.get('lastPr') is None:
            return 0
        price = float(data.get('lastPr'))
        return price

    def get_account_balance(self) -> AccountBalance:
        """
        Get account balances, falling back to marginCoin if needed.
        """

        endpoint = '/api/v2/spot/account/assets'
        if self.account_type == "U":
            endpoint = '/api/v2/mix/account/accounts?productType=USDT-FUTURES'
        elif self.account_type  == "C":
            endpoint = '/api/v2/mix/account/accounts?productType=COIN-FUTURES'
        elif self.account_type  == "UC":
            endpoint = '/api/v2/mix/account/accounts?productType=USDC-FUTURES'

        balances = {}

        response = self.send_request('GET', endpoint)
        if 'code' in response and int(response['code']) != 0:
            raise ValueError(response['msg'])
        
        for asset in response['data']:
            coin_key = asset.get('coin') or asset.get('marginCoin')
            balances[coin_key] = {
                'available': float(asset.get('available', 0)),
                'locked': float(asset.get('locked', 0)),
            }
            
        return balances

    def open_trade(self, symbol, side, quantity, custom_id = '', oc = 'open') -> OpenTrade:
        try:
            # Endpoint for placing an order
            endpoint = '/api/v2/spot/trade/place-order'
            if self.account_type == "U":
                productType = "USDT-FUTURES"
                endpoint = '/api/v2/mix/order/place-order'
            elif self.account_type == "C":
                productType = "COIN-FUTURES"
                endpoint = '/api/v2/mix/order/place-order'
            elif self.account_type == "UC":
                productType = "USDC-FUTURES"
                endpoint = '/api/v2/mix/order/place-order'

            sys_info = self.get_exchange_info(symbol)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            base_asset = sys_info.get('base_asset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity =  self.adjust_trade_quantity(sys_info, side, float(quantity))
            print("Adjusted quantity:", adjusted_quantity)

            if float(adjusted_quantity) <= 0:
                raise ValueError("Insufficient balance for the trade.")

            body = {
                "symbol": order_symbol,
                "side": side.upper(),
                "orderType": "MARKET",
                "size": adjusted_quantity  # Ensure this is the base coin amount
            }

            if self.account_type == 'U':
                currency_asset = "USDT"
                body["productType"] = productType
                body["marginMode"] = "isolated"
                body["marginCoin"] = currency_asset
                body["tradeSide"] = oc
            elif self.account_type == 'C':
                currency_asset = "USDE"
                body["productType"] = productType
                body["marginMode"] = "isolated"
                body["marginCoin"] = currency_asset
                body["tradeSide"] = oc
            elif self.account_type == 'UC':
                currency_asset = "USDC"
                body["productType"] = productType
                body["marginMode"] = "isolated"
                body["marginCoin"] = currency_asset
                body["tradeSide"] = oc

            if self.account_type != 'S':
                try:
                    self.send_request('POST', '/api/v2/mix/account/set-position-mode', {'posMode': 'hedge_mode', 'productType': productType})
                except Exception as e:
                    print("Error setting position mode or coin:", str(e))

            # print("body ==> ", body)

            # Send the trade request
            response = self.send_request('POST', endpoint, body)

            if "msg" in response and response.get('code') != '00000':
                raise Exception(response.get('msg'))
            
            response = response.get('data')
            order_id = response.get("orderId")

            if order_id is None:
                raise Exception("Order ID not found in response")
            
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
                    'symbol': symbol,
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
                    'message': f"Trade opened with order ID {response.get('orderId')}.",
                    'order_id': response.get('orderId'),
                    'closed_order_id': response.get('orderId'),
                    'symbol': response.get('symbol', symbol),
                    "side": side.upper(),
                    'price': 0,
                    # 'fees': response['fills'][0]['commission'],
                    'qty': adjusted_quantity,
                    'currency': currency_asset,
                }
            
        
        except Exception as e:
            print('error opening bitget trade: ', str(e))
            return {'error': str(e)}

    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        if self.account_type == "S":
            opposite_side = "sell" if side.lower() == "buy" else "buy"
        else:
            opposite_side = side.lower()
        try:
            trade = self.open_trade(symbol, opposite_side, quantity, oc = 'close')
            if trade.get('error') is not None:
                raise Exception(trade.get('error'))
            return trade
        except Exception as e:
            return {'error': str(e)}


    def get_order_info(self, symbol, order_id) -> OrderInfo:
        try:
            order_endpoint = '/api/v2/spot/trade/fills'

            if self.account_type == "U":
                productType = "USDT-FUTURES"
                order_endpoint = '/api/v2/mix/order/fills'

            elif self.account_type == "C":
                productType = "COIN-FUTURES"
                order_endpoint = '/api/v2/mix/order/fills'

            elif self.account_type == "UC":
                productType = "USDC-FUTURES"
                order_endpoint = '/api/v2/mix/order/fills'
            

            order_url = order_endpoint + f"?orderId={order_id}"

            if self.account_type != 'S':
                order_url += f"&productType={productType}&symbol={symbol}"

            response = self.send_request('GET', order_url)
            # print("trade data => ", response) 
            response = response.get('data')

            if self.account_type != 'S':
                response = response.get('fillList')

            
            if response is None:
                raise ValueError("No data found in response")
            

            if isinstance(response, list):
                if len(response) > 1:
                    total_qty = sum(float(t.get('size', 0)) for t in response)
                    # Use the last fill as the base record
                    trade = response[-1]
                    trade['size'] = str(total_qty)
                    
                    # Sum total_commission across all fills, handling list or dict in feeDetail
                    total_commission = 0.0
                    for t in response:
                        fd = t.get('feeDetail', {})
                        if isinstance(fd, list):
                            for entry in fd:
                                total_commission += float(entry.get('totalFee', 0))
                        elif isinstance(fd, dict):
                            total_commission += float(fd.get('totalFee', 0))
                    fee_detail = trade.get('feeDetail')
                    if not isinstance(fee_detail, dict):
                        fee_detail = {}
                    fee_detail['totalFee'] = str(total_commission)
                    trade['feeDetail'] = fee_detail
                else:
                    trade = response[0]
            else:
                trade = response
            

            if trade:

                sym_info = self.get_exchange_info(symbol)
                # Fallback to 'price' if 'priceAvg' is missing or falsy
                price_str = trade.get('priceAvg') or trade.get('price', '0')
                price_usdt = Decimal(str(price_str))

                # Normalize fee detail, which may be a dict or a list of dicts
                fee_detail = trade.get('feeDetail', {})
                total_fees = Decimal('0')

                if isinstance(fee_detail, list):
                    # Sum and convert each fee entry
                    for fd in fee_detail:
                        amt = Decimal(str(fd.get('totalFee', '0')))
                        coin = fd.get('feeCoin')
                        if coin == sym_info.get('base_asset'):
                            total_fees += amt * price_usdt
                        else:
                            total_fees += amt
                else:
                    amt = Decimal(str(fee_detail.get('totalFee', '0')))
                    coin = fee_detail.get('feeCoin')
                    if coin == sym_info.get('base_asset'):
                        total_fees = amt * price_usdt
                    else:
                        total_fees = amt

                # Use the computed total_fees
                fees = total_fees
                
                r = {
                    'order_id': str(trade.get('orderId')),
                    'symbol': str(trade.get('symbol')),
                    'volume': str(trade.get('size') or trade.get('baseVolume')),
                    'side': str(trade.get('side')),
                    
                    'time': self.convert_timestamp(trade.get('cTime')),
                    'price': str(price_str),

                    'profit': str(trade.get('profit')),

                    'fees': str(abs(fees)),

                    'additional_info': str(trade.get('feeDetail')),
                }

                return r 
            
            return None

        except Exception as e:
            print('error getting order details: ', str(e))
            return None
        
