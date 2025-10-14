
from bitmart.api_spot import APISpot
from bitmart.api_contract import APIContract
from bitmart.lib import cloud_exceptions

import json
import time

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

class BitmartClient(CryptoBrokerClient):
    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        super().__init__(account=account, api_key=api_key, api_secret=api_secret, passphrase=passphrase, account_type=account_type, current_trade=current_trade)

        if self.account_type == "S":
            self.API = APISpot(self.api_key, self.api_secret, self.passphrase, timeout=(3, 10))
        else:
            self.API = APIContract(self.api_key, self.api_secret, self.passphrase, timeout=(3, 10))


    @staticmethod
    def check_credentials(api_key, api_secret, passphrase, account_type="S"):
        """Check the validity of the Bitmart API credentials without instantiating."""
        try:
            client = BitmartClient(api_key=api_key, api_secret=api_secret, passphrase=passphrase, account_type=account_type)
            if client.account_type == 'S':
                response = client.API.get_wallet()
            else:
                response = client.API.get_assets_detail()

            if response[0]['code'] != 1000:
                return {'error': response[0].get('message'), 'valid': False}
            
            return {'message': "API credentials are valid.", 'valid': True}
        except cloud_exceptions.APIException as apiException:
            error = json.loads(apiException.response)
            error_msg = error.get('msg') or error.get('message', 'API credentials are not valid.')
            return {'error': error_msg, 'valid': False}
        except Exception as e:
            return {'error': str(e), 'valid': False}
        
    
    def get_exchange_info(self, symbol) -> ExchangeInfo:

        try:
            symbol = self.adjust_symbol_name(symbol)
            
            if self.account_type == 'S':
                response = self.API.get_symbol_detail()
            else:
                response = self.API.get_details(contract_symbol=symbol)

            if response[0].get('code') != 1000:
                raise Exception(response[0].get('message'))
            else:
                symbols = response[0].get('data', {}).get('symbols', [])

            target = symbol.upper()
            for item in symbols:
                inst = item.get('symbol', '')
                if inst.replace('_', '').upper() == target or inst == target:
                    # print(item)
                    base_asset = item.get('base_currency')
                    quote_asset = item.get('quote_currency')

                    min_base_amnt = item.get('base_min_size') or item.get('contract_size')
                    min_quote_amnt = item.get('min_buy_amount') or item.get('price_precision')

                    base_decimals = self.get_decimals_from_step(min_base_amnt)
                    quote_decimals = item.get('price_min_precision') or self.get_decimals_from_step(min_quote_amnt)

                    return {
                        'symbol': item.get('symbol'),
                        'base_asset': base_asset,
                        'quote_asset': quote_asset,
                        'base_decimals': base_decimals,
                        'quote_decimals': quote_decimals,
                    }

            raise Exception("Symbol not found")

        except cloud_exceptions.APIException as apiException:
            error = json.loads(apiException.response)
            error_msg = error.get('msg') or error.get('message', 'Symbol not found.')
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(str(e))
        
    def get_current_price(self, symbol):
        try:
            if self.account_type == 'S':
                response = self.API.get_v3_ticker(symbol)
                
                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('message'))
                else:
                    sy = response[0].get('data', {})
                    return sy.get('bid_px')

            else:
                response = self.API.get_details(contract_symbol=symbol)

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('msg'))
                else:
                    symbols = response[0].get('data', {}).get('symbols', [])

                # print(response)

                target = symbol.upper()
                for item in symbols:
                    inst = item.get('symbol', '')

                    if inst.replace('_', '').upper() == target or inst == target:
                        return item.get('last_price', None) or item.get('index_price', 0)

            raise Exception("Symbol not found")

        except cloud_exceptions.APIException as apiException:
            error = json.loads(apiException.response)
            error_msg = error.get('msg') or error.get('message', 'Symbol not found.')
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(str(e))


    def get_account_balance(self, symbol:str = None) -> AccountBalance:
        try:
            balances = {}

            if self.account_type == "S":  # Spot
                response = self.API.get_wallet()
                # print(response)

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('message'))
                else:
                    wallet = response[0].get('data', {}).get('wallet', [])

                for balance in wallet:
                    if symbol and balance['id'].upper() not in symbol.upper():
                        continue
                    balances[balance['id']] = {
                        'available': float(balance['available']),
                        'locked': float(balance['frozen'])
                    }
            else:
                response = self.API.get_assets_detail()
                # print(response)

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('msg'))
                else:
                    wallet = response[0].get('data', [])

                for balance in wallet:
                    if symbol and balance['currency'].upper() not in symbol.upper():
                        continue
                    balances[balance['currency']] = {
                        'available': float(balance['available_balance']),
                        'locked': float(balance['frozen_balance'])
                    }

            return balances

        except cloud_exceptions.APIException as apiException:
            error = json.loads(apiException.response)
            error_msg = error.get('msg') or error.get('message', 'Error getting account balance.')
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(str(e))


    def open_trade(self, symbol, side, quantity, custom_id = '', oc = False) -> OpenTrade:
        try:

            sys_info = self.get_exchange_info(symbol)
            print(sys_info)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity =  self.adjust_trade_quantity(sys_info, side, quantity)

            print("Adjusted quantity:", adjusted_quantity)

            end_exe = None

            if self.account_type == 'S':
                order_params = {
                    "symbol": order_symbol,
                    "side": str.lower(side),
                    "type": "MARKET",
                }

                if str.lower(side) == 'buy':
                    order_params['notional'] = adjusted_quantity
                if str.lower(side) == 'sell':
                    order_params['size'] = adjusted_quantity

                response = self.API.post_submit_order(**order_params)

                end_exe = time.perf_counter()

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('message'))
                else:
                    order_id = response[0].get('data', {}).get('order_id', '')

                if not self.current_trade:
                    order_details = self.get_order_info(order_symbol, order_id)
                    trade_details = None 
                else :
                    order_details = self.get_final_trade_details(self.current_trade, order_id)
                    trade_details = order_details

            else:
                currency_asset = sys_info.get('quote_asset')
                if currency_asset == 'USD':
                    currency_asset = sys_info.get('base_asset')
                # try:
                #     self.API.set_pos
                
                # except cloud_exceptions.APIException as apiException:
                #     print(f"Error switching position mode: ${apiException.response}")

                _side = 1 if str.upper(side) == "BUY" else 4 if str.upper(side) == "SELL" else 0
                if oc:
                    _side = 2 if str.upper(side) == "BUY" else 3 if str.upper(side) == "SELL" else 0

                order_params = {
                    "contract_symbol": order_symbol,
                    "side": _side,
                    "type": "market",
                    "size": int(float(adjusted_quantity)),
                }
                response = self.API.post_submit_order(**order_params)

                end_exe = time.perf_counter()

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('msg'))
                else:
                    order_id = response[0].get('data', {}).get('order_id', '')

                if not self.current_trade:
                    order_details = self.get_order_info(order_symbol, str(order_id))
                    trade_details = None 
                else :
                    order_details = self.get_final_trade_details(self.current_trade, str(order_id))
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

                    'trade_details': trade_details,
                    "end_exe": end_exe
                }
            
            else:
                return {
                    'message': f"Trade opened with order ID {order_id}.",
                    'order_id': order_id,
                    'closed_order_id': order_id,
                    'symbol': symbol,
                    "side": side.upper(),
                    'qty': adjusted_quantity,
                    'currency': currency_asset,
                    "end_exe": end_exe
                }

        except cloud_exceptions.APIException as apiException:
            error = json.loads(apiException.response)
            # print(apiException)
            error_msg = error.get('msg') or error.get('message', 'An error occured!')
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(str(e))


    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        opposite_side = "sell" if side.lower() == "buy" else "buy"

        return self.open_trade(symbol, opposite_side, quantity, oc=True)
    

    def get_order_info(self, symbol, order_id) -> OrderInfo:
        try:
            if self.account_type == 'S':
                response = self.API.v4_query_order_trade_list(order_id=order_id)

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('message'))
                else:
                    trade = response[0].get('data', [])[0]

                if trade:
                    # print('Trade details:', trade)
                    # Fallback to 'price' if 'priceAvg' is missing or falsy
                    price_str = trade.get('price')

                    # Normalize fee detail, which may be a dict or a list of dicts
                    fees = trade.get('fee', 0)
                    fees = self.calculate_fees(symbol, price_str, fees, trade.get('feeCoinName'))
                    
                    r = {
                        'order_id': str(trade.get('orderId')),
                        'symbol': str(trade.get('symbol')),
                        'volume': str(trade.get('size')),
                        'side': str(trade.get('side')),
                        
                        'time': self.convert_timestamp(trade.get('createTime')),
                        'price': str(price_str),

                        'profit': str(trade.get('profit', None)),

                        'fees': str(abs(fees)),

                        'additional_info': {
                            'fee': str(trade.get('fee')),
                            'feeCoinName': str(trade.get('feeCoinName')),
                            'orderMode': str(trade.get('orderMode')),
                        }
                    }

                    return r 
                
            else:
                time.sleep(2)
                response = self.API.get_trades(contract_symbol=symbol)

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('msg'))
                else:
                    trades = response[0].get('data', [])
                    trade = next((item for item in trades if item.get('order_id') == order_id), None)

                    # print(trade)

                    if trade:
                        r = {
                            'order_id': str(trade.get('order_id')),
                            'symbol': str(trade.get('symbol')),
                            'volume': str(trade.get('vol')),
                            'side': str(trade.get('side')),
                            
                            'time': self.convert_timestamp(trade.get('create_time')),
                            'price': str(trade.get('price')),

                            'profit': str(trade.get('realised_profit', None)),

                            'fees': str(trade.get('paid_fees')),

                            'additional_info': {
                                'account': str(trade.get('account')),
                                'exec_type': str(trade.get('exec_type')),
                            }
                        }

                        return r 
            
            return None
        
        except cloud_exceptions.APIException as apiException:
            error = json.loads(apiException.response)
            error_msg = error.get('msg') or error.get('message', 'Error getting trade data.')
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(str(e))


    def get_trading_pairs(self):
        try:
            pairs = []

            if self.account_type == 'S':
                response = self.API.get_symbol_detail()

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('message'))
                else:
                    symbols = response[0].get('data', {}).get('symbols', [])

                for item in symbols:
                    pairs.append(item.get('symbol'))

            else:
                response = self.API.get_details()

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('msg'))
                else:
                    symbols = response[0].get('data', {}).get('symbols', [])

                for item in symbols:
                    pairs.append(item.get('symbol'))

            return pairs

        except cloud_exceptions.APIException as apiException:
            error = json.loads(apiException.response)
            error_msg = error.get('msg') or error.get('message', 'Error fetching trading pairs.')
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(str(e))
        

    def get_history_candles(self, symbol, interval, limit = 500):
        try:
            #  [1, 3, 5, 15, 30, 45, 60, 120, 180, 240, 1440, 10080, 43200]
            bitmart_intervals = {
                '1m': '1',
                '3m': '3',
                '5m': '5',
                '15m': '15',
                '30m': '30',
                '45m': '45',
                '1h': '60',
                '2h': '120',
                '3h': '180',
                '4h': '240',
                '1d': '1440',
                '1W': '10080',
                '1M': '43200'
            }
            step = bitmart_intervals.get(interval, '1')

            # print("Fetching candles for", symbol, "interval", interval, "step", step)

            if self.account_type == 'S':
                response = self.API.get_v3_latest_kline(symbol=symbol, step=step, limit=limit)

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('message'))
                else:
                    data = response[0].get('data', [])

                candles = []
                for entry in data:
                    # print(entry)
                    candles.append({
                        "time": self.convert_timestamp(int(entry[0]) * 1000),
                        # "timestamp": int(entry[0]) * 1000,
                        "open": float(entry[1]),  # open
                        "high": float(entry[2]),  # high
                        "low": float(entry[3]),  # low
                        "close": float(entry[4]),  # close
                        "volume": float(entry[5])   # volume
                    })
                return candles

            else:
                end_time = int(time.time())
                start_time = end_time - (limit * int(step) * 60)

                response = self.API.get_kline(contract_symbol=symbol, step=step, start_time=start_time, end_time=end_time)

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('msg'))
                else:
                    data = response[0].get('data', [])

                # print("Candle data:", data)

                candles = []
                for entry in data:
                    candles.append({
                        "time": self.convert_timestamp(int(entry.get('timestamp')) * 1000),
                        # "timestamp": int(entry.get('timestamp')) * 1000,
                        "open": float(entry.get('open_price')),  # open
                        "high": float(entry.get('high_price')),  # high
                        "low": float(entry.get('low_price')),  # low
                        "close": float(entry.get('close_price')),  # close
                        "volume": float(entry.get('volume'))   # volume
                    })
                return candles

        except cloud_exceptions.APIException as apiException:
            error = json.loads(apiException.response)
            error_msg = error.get('msg') or error.get('message', 'Error fetching historical candles.')
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(str(e))
        

    def get_order_book(self, symbol, limit = 100):
        try:
            if self.account_type == 'S':
                response = self.API.get_v3_depth(symbol, limit=limit)

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('message'))
                else:
                    data = response[0].get('data', {})

                bids = [{"price":float(price), "qty":float(quantity)} for price, quantity in data.get('bids', [])],
                asks = [{"price":float(price), "qty":float(quantity)} for price, quantity in data.get('asks', [])],

                return {'bids': bids, 'asks': asks}

            else:
                response = self.API.get_depth(contract_symbol=symbol)

                if response[0].get('code') != 1000:
                    raise Exception(response[0].get('msg'))
                else:
                    data = response[0].get('data', {})

                # bids = [{"price":float(price), "qty":float(quantity)} for price, quantity in data.get('bids', [])],
                # asks = [{"price":float(price), "qty":float(quantity)} for price, quantity in data.get('asks', [])],

                return data
            
        except cloud_exceptions.APIException as apiException:
            error = json.loads(apiException.response)
            error_msg = error.get('msg') or error.get('message', 'Error fetching order book.')
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(str(e))