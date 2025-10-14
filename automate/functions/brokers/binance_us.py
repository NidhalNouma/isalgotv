import requests
import time
from automate.functions.brokers.types import *
from automate.functions.brokers.broker import CryptoBrokerClient

class BinanceUSClient(CryptoBrokerClient):
    API_URL = 'https://api.binance.us'

    def _send_request(self, method, endpoint, params={}, with_signuture = True):
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        timestamp = self._get_timestamp()
        
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        if with_signuture:
            query_string += f"&timestamp={timestamp}"
            signature = self._create_signature(query_string)
            query_string += f"&signature={signature}"

        url = f"{self.API_URL}{endpoint}?{query_string}"
        response = requests.request(method, url, headers=headers)
        return response.json()


    @staticmethod
    def check_credentials(api_key, api_secret, account_type='S'):
        try:
            client = BinanceUSClient(api_key=api_key, api_secret=api_secret)
            response = client._send_request('GET', '/api/v3/account')
            if response.get('code') == -2014:  # Example error code handling
                return {'error': "Invalid API key or secret.", "valid": False}
            return {'message': "API credentials are valid.", "valid": True}
        except Exception as e:
            return {'error': str(e)}
        
    def get_exchange_info(self, symbol) -> ExchangeInfo:
        try:
            symbol = self.adjust_symbol_name(symbol)
            params = {
                "symbol": symbol,
            }
            response = self._send_request('GET', '/api/v3/exchangeInfo', params, False)

                    
            if isinstance(response, list):
                data_list = response
            else:
                data_list = response.get('symbols', [])
            
            target = symbol.upper()
            for item in data_list:
                # print("Checking item:", item, target)
                inst = item.get('symbol', '')
                if inst.replace('_', '').upper() == target or inst == target:
                    symbol_info = item

                    base_asset = symbol_info.get('baseAsset')
                    quote_asset = symbol_info.get('quoteAsset')

                    # find the filters
                    price_filter = next(f for f in symbol_info['filters'] if f['filterType']=='PRICE_FILTER')
                    lot_filter   = next(f for f in symbol_info['filters'] if f['filterType']=='LOT_SIZE')

                    quote_decimals = self.get_decimals_from_step(price_filter['tickSize'])
                    base_decimals   = self.get_decimals_from_step(lot_filter['stepSize'])

                    return {
                        'symbol': symbol_info.get('symbol'),
                        'base_asset': base_asset,
                        'quote_asset': quote_asset,
                        'base_decimals': base_decimals,
                        'quote_decimals': quote_decimals,
                    }
            return None
        except Exception as e:
            print('Error getting exchange info:', e)
            raise Exception(f"Error getting exchange info for {symbol}: {str(e)}")

    def get_account_balance(self) -> AccountBalance:
        try:
            """Fetch the available balance for a specific asset."""
            response = self._send_request('GET', '/api/v3/account')
            balances = {item['asset']: {'available': float(item['free']), 'locked': 0} for item in response['balances']}
            # print("Account balances:", balances)
            return balances
        except Exception as e:
            print('Error getting account balance:', e)
            raise Exception(f"Error getting account balance: {str(e)}")
        
    def open_trade(self, symbol, side, quantity, custom_id = '') -> OpenTrade:
        try:

            symbol_info = self.get_exchange_info(symbol)

            if not symbol_info:
                raise Exception('Symbol was not found!')
            
            print("Symbol info:", symbol_info)

            adjusted_quantity = self.adjust_trade_quantity(symbol_info, side, quantity)

            quote_asset = symbol_info.get('quote_asset')
            order_symbol = symbol_info.get('symbol')

            params = {
                "symbol": order_symbol,
                "side": side.upper(),
                "type": "MARKET",
                "quantity": adjusted_quantity,
                # "quoteOrderQty": adjusted_quantity
            }

            print("Quantity:", quantity, "Qty:", adjusted_quantity)

            response = self._send_request('POST', '/api/v3/order', params)

            end_exe = time.perf_counter()
            
            if response.get('msg') is not None:
                raise Exception(response.get('msg'))
            
            
            order_id = response.get("orderId")
            order_details = self.get_order_info(symbol, order_id)

            print("Order details:", order_details)

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
                    "end_exe": end_exe
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
                    "end_exe": end_exe
                }

        except Exception as e:
            print('Error opening trade:', e)
            return {'error': str(e)}

    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        try:
            symbol_info = self.get_exchange_info(symbol)

            if not symbol_info:
                raise Exception('Symbol was not found!')

            adjusted_quantity = self.adjust_trade_quantity(symbol_info, t_side, quantity)

            params = {
                "symbol": symbol,
                "side": t_side,
                "type": "MARKET",

                "quantity": adjusted_quantity
                # "quoteOrderQty": adjusted_quantity
            }

            print("Quantity:", quantity, "Qty:", adjusted_quantity)

            response = self._send_request('POST', '/api/v3/order', params)

            end_exe = time.perf_counter()

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
                "end_exe": end_exe
            }
        except Exception as e:        
            return {'error': str(e)}
        
    def get_order_info(self, symbol, order_id) -> OrderInfo:
        try:

            params = {
                "symbol": symbol,
                "orderId": order_id,
            }

            response = self._send_request('GET', '/api/v3/myTrades', params)

            # print("Response from get_order_info:", response)

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
                }
            }

            return r
        except Exception as e:     
            print('getting trade info ', e)   
            return None

    def get_current_price(self, symbol):
        try:
            params = {
                "symbol": symbol,
            }
            response = self._send_request('GET', '/api/v3/ticker/price', params, False)
            if response.get('code') == -1121:  # Example error code handling
                raise Exception("Symbol not found.")
            return float(response['price'])
        except Exception as e:
            print('Error getting exchange price:', e)
            raise Exception(f"Error getting exchange price for {symbol}: {str(e)}")
        
    def get_history_candles(self, symbol, interval, limit = 500):
        try:
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = self._send_request('GET', '/api/v3/klines', params, False)

            if isinstance(response, dict) and response.get('code') is not None:
                raise Exception(response.get('msg', 'Error fetching candles'))

            candles = []
            for item in response:
                candle = {
                    'open_time': self.convert_timestamp(item[0]),
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5]),
                    'close_time': self.convert_timestamp(item[6]),
                    'quote_asset_volume': float(item[7]),
                    'number_of_trades': int(item[8]),
                    'taker_buy_base_asset_volume': float(item[9]),
                    'taker_buy_quote_asset_volume': float(item[10]),
                }
                candles.append(candle)
            return candles
        except Exception as e:
            print('Error getting historical candles:', e)
            raise Exception(f"Error getting historical candles for {symbol}: {str(e)}")

    def get_order_book(self, symbol, limit = 100):
        try:
            params = {
                "symbol": symbol,
                "limit": limit
            }
            response = self._send_request('GET', '/api/v3/depth', params, False)

            if isinstance(response, dict) and response.get('code') is not None:
                raise Exception(response.get('msg', 'Error fetching order book'))

            bids = [[float(price), float(qty)] for price, qty in response.get('bids', [])]
            asks = [[float(price), float(qty)] for price, qty in response.get('asks', [])]

            return {
                'lastUpdateId': response.get('lastUpdateId'),
                'bids': bids,
                'asks': asks
            }
        except Exception as e:
            print('Error getting order book:', e)
            raise Exception(f"Error getting order book for {symbol}: {str(e)}")

    def get_trading_pairs(self):
        try:
            response = self._send_request('GET', '/api/v3/exchangeInfo', {}, False)

            symbols = []
            for item in response.get('symbols', []):
                symbols.append(item['symbol'])
            return symbols
        except Exception as e:
            print('Error getting trading pairs:', e)
            raise Exception(f"Error getting trading pairs: {str(e)}")


