import time
import hmac
import hashlib
import requests

from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP

from .broker import BrokerClient

class BinanceUSClient(BrokerClient):
    API_URL = 'https://api.binance.us'

    def __init__(self, account=None, api_key=None, api_secret=None, account_type="S", current_trade=None):
        if account is not None:
            self.api_key = account.apiKey
            self.api_secret = account.secretKey
            self.passphrase = account.pass_phrase
            self.account_type = getattr(account, 'type', None)
        else:
            self.api_key = api_key
            self.api_secret = api_secret
            self.trade_type = account_type

        self.current_trade = current_trade

    def create_signature(self, query_string):
        return hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()


    def send_request(self, method, endpoint, params={}, with_signuture = True):
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        timestamp = int(time.time() * 1000)
        
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        if with_signuture:
            query_string += f"&timestamp={timestamp}"
            signature = self.create_signature(query_string)
            query_string += f"&signature={signature}"

        url = f"{self.API_URL}{endpoint}?{query_string}"
        response = requests.request(method, url, headers=headers)
        return response.json()


    @staticmethod
    def check_credentials(api_key, api_secret):
        try:
            client = BinanceUSClient(api_key=api_key, api_secret=api_secret)
            response = client.send_request('GET', '/api/v3/account')
            if response.get('code') == -2014:  # Example error code handling
                return {'error': "Invalid API key or secret.", "valid": False}
            return {'message': "API credentials are valid.", "valid": True}
        except Exception as e:
            return {'error': str(e)}
        
    def get_exchange_info(self, symbol):
        params = {
            "symbol": symbol,
        }
        response = self.send_request('GET', '/api/v3/exchangeInfo', params, False)
                
        if isinstance(response, list):
            data_list = response
        else:
            data_list = response.get('symbols', [])
        
        target = symbol.upper()
        for item in data_list:
            inst = item.get('symbol', '')
            if inst.replace('_', '').upper() == target or inst == target:
                return item
        return None

    def get_account_balance(self):
        """Fetch the available balance for a specific asset."""
        response = self.send_request('GET', '/api/v3/account')
        balances = {item['asset']: float(item['free']) for item in response['balances']}
        balances
        
    def adjust_trade_quantity(self, symbol_info, quote_order_qty, trade_type):
        """Adjust the trade quantity based on available balance."""
        try:
            base_asset = symbol_info.get('baseAsset')
            quote_asset = symbol_info.get('quoteAsset')

            # find the filters
            price_filter = next(f for f in symbol_info['filters'] if f['filterType']=='PRICE_FILTER')
            lot_filter   = next(f for f in symbol_info['filters'] if f['filterType']=='LOT_SIZE')

            quote_decimals = self.get_decimals_from_step(price_filter['tickSize'])
            base_decimals   = self.get_decimals_from_step(lot_filter['stepSize'])

            balances = self.get_account_balance()

            base_balance = balances.get(base_asset, 0)
            quote_balance = balances.get(quote_asset, 0)

            # print(symbol_info)
            # print(base_decimals, price_filter, quote_decimals)

            try:
                precision = int(base_decimals)
            except (TypeError, ValueError):
                precision = 8  # fallback precision
            quant = Decimal(1).scaleb(-precision)  
            
            if trade_type.upper() == "BUY":

                if float(quote_balance) <= 0:
                    raise ValueError("Insufficient quote balance.")
                # elif quote_balance < quote_order_qty:
                #     return quote_balance
                # Format quantity to max base_decimals and return as string
                qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                return format(qty_dec, f'.{precision}f')
            
            elif trade_type.upper() == "SELL":
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
            print('adjust trade quantity error: ', str(e))
            return quote_order_qty


    def open_trade(self, symbol, side, quantity, custom_id):
        try:

            symbol_info = self.get_exchange_info(symbol)

            if not symbol_info:
                raise Exception('Symbol was not found!')

            adjusted_quantity = self.adjust_trade_quantity(symbol_info, float(quantity), side)

            quote_asset = symbol_info.get('quoteAsset')
            order_symbol = symbol_info.get('symbol')

            params = {
                "symbol": order_symbol,
                "side": side.upper(),
                "type": "MARKET",
                "quantity": adjusted_quantity,
                # "quoteOrderQty": adjusted_quantity
            }

            print("Quantity:", quantity, "Qty:", adjusted_quantity)

            response = self.send_request('POST', '/api/v3/order', params)
            
            if response.get('msg') is not None:
                raise Exception(response.get('msg'))
            
            
            order_id = response.get("orderId")
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
                'message': f"Trade opened with order ID {response.get('orderId')}.",
                'order_id': response.get('orderId'),
                'symbol': response.get('symbol', symbol),

                'price': response['fills'][0]['price'],
                # 'fees': response['fills'][0]['commission'],
                'qty': response.get('executedQty', adjusted_quantity),
                'currency': quote_asset,
                }

        except Exception as e:
            return {'error': str(e)}

    def close_trade(self, symbol, side, quantity):
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        try:
            
            symbol_info = self.get_exchange_info(symbol)

            if not symbol_info:
                raise Exception('Symbol was not found!')

            adjusted_quantity = self.adjust_trade_quantity(symbol_info, float(quantity), side)

            params = {
                "symbol": symbol,
                "side": t_side,
                "type": "MARKET",

                "quantity": adjusted_quantity
                # "quoteOrderQty": adjusted_quantity
            }

            print("Quantity:", quantity, "Qty:", adjusted_quantity)

            response = self.send_request('POST', '/api/v3/order', params)

            if response.get('msg') is not None:
                raise Exception(response.get('msg'))

            return {
                'message': f"Trade closed for order ID {response.get('orderId')}.",
                "symbol": symbol,

                "id": response.get('orderId'),
                "closed_order_id": response["orderId"],
                "side": t_side.upper(),
                'price': response['fills'][0]['price'],
                'qty': response.get('executedQty', adjusted_quantity),
            }
        except Exception as e:        
            return {'error': str(e)}
        
    def get_order_info(self, symbol, order_id):
        try:

            params = {
                "symbol": symbol,
                "orderId": order_id,
            }

            response = self.send_request('GET', '/api/v3/myTrades', params)

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
                }
            }

            return r
        except Exception as e:     
            print('getting trade info ', e)   
            return None

