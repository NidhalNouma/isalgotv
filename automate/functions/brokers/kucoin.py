# if account type == F it uses the contract value as the size of the trade and not the base asset

import time
import math
from datetime import datetime, timezone
from kucoin_universal_sdk.api import DefaultClient
from kucoin_universal_sdk.generate.spot.market import GetSymbolReqBuilder, GetTickerReqBuilder, GetAllSymbolsReqBuilder, GetKlinesReqBuilder, GetPartOrderBookReqBuilder
from kucoin_universal_sdk.generate.spot.order import AddOrderReqBuilder, GetTradeHistoryReqBuilder, GetOrderByOrderIdReqBuilder
from kucoin_universal_sdk.generate.futures.market import GetSymbolReqBuilder as GetFutureSymbolReqBuilder, GetKlinesReqBuilder as GetFutureKlinesReqBuilder, GetPartOrderBookReqBuilder as GetFuturePartOrderBookReqBuilder
from kucoin_universal_sdk.generate.futures.order import AddOrderReqBuilder as AddFutureOrderReqBuilder, GetTradeHistoryReqBuilder as GetFutureTradeHistoryReqBuilder
from kucoin_universal_sdk.generate.futures.positions import GetPositionsHistoryReqBuilder
from kucoin_universal_sdk.generate.account.account import GetSpotAccountListReqBuilder, GetFuturesAccountReqBuilder
from kucoin_universal_sdk.model import ClientOptionBuilder
from kucoin_universal_sdk.model import GLOBAL_API_ENDPOINT, GLOBAL_FUTURES_API_ENDPOINT, \
    GLOBAL_BROKER_API_ENDPOINT
from kucoin_universal_sdk.model import TransportOptionBuilder

from kucoin_universal_sdk.model.common import RestError

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *


class KucoinClient(CryptoBrokerClient):
    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        super().__init__(account, api_key, api_secret, passphrase, account_type, current_trade)

        http_transport_option = (
            TransportOptionBuilder()
                .set_keep_alive(True)
                .set_max_pool_size(10)
                .set_max_connection_per_pool(10)
                .build()
            )

        # Create a client using the specified options
        client_option = (
            ClientOptionBuilder()
            .set_key(self.api_key)
            .set_secret(self.api_secret)
            .set_passphrase(self.passphrase)
            .set_spot_endpoint(GLOBAL_API_ENDPOINT)
            .set_futures_endpoint(GLOBAL_FUTURES_API_ENDPOINT)
            .set_broker_endpoint(GLOBAL_BROKER_API_ENDPOINT)
            .set_transport_option(http_transport_option)
            .build()
        )
        self.rest_service = DefaultClient(client_option).rest_service()

    @staticmethod
    def check_credentials(api_key, api_secret, passphrase, account_type='S'):
        try:
            client = KucoinClient(api_key=api_key, api_secret=api_secret, passphrase=passphrase)
            rest_service = client.rest_service

            spot_account_api = rest_service.get_account_service().get_account_api()

            response = spot_account_api.get_account_info().to_dict()
            response = response.get('common_response')

            # print(response)
            if response.get('code') != "200000":  # Example error code handling
                return {'error': "Invalid API key or secret.", "valid": False}
            return {'message': "API credentials are valid.", "valid": True}
        except RestError as e:
            # print('error msf', e.msg)
            return {'error': str(e.msg)}
        except Exception as e:
            return {'error': str(e)}
        
    def get_exchange_info(self, symbol) -> ExchangeInfo:
        try:
            symbol = self.adjust_symbol_name(symbol)
            if self.account_type == 'S':
                symbol_req = GetSymbolReqBuilder().set_symbol(symbol).build()
                request = self.rest_service.get_spot_service().get_market_api()

                response = request.get_symbol(symbol_req).to_dict()
                response = response.get('common_response')

                sym_info = response.get('data', {})
                # print(sym_info, type(sym_info), sym_info)
                if sym_info:
                    base_asset = sym_info.get('baseCurrency')
                    quote_asset = sym_info.get('quoteCurrency')

                    base_decimals = self.get_decimals_from_step(sym_info.get('baseIncrement'))
                    quote_decimals = self.get_decimals_from_step(sym_info.get('quoteIncrement'))

                    return {
                        'symbol': sym_info.get('symbol'),
                        'base_asset': base_asset,
                        'quote_asset': quote_asset,
                        'base_decimals': base_decimals,
                        'quote_decimals': quote_decimals,
                    }
            else:
                symbol_req = GetFutureSymbolReqBuilder().set_symbol(symbol).build()
                request = self.rest_service.get_futures_service().get_market_api()
                response = request.get_symbol(symbol_req).to_dict()

                response = response.get('common_response')
                sym_info = response.get('data', {})
                
                if sym_info:
                    base_asset = sym_info.get('baseCurrency')
                    quote_asset = sym_info.get('quoteCurrency')

                    base_decimals = self.get_decimals_from_step(sym_info.get('tickSize'))
                    quote_decimals = self.get_decimals_from_step(sym_info.get('indexPriceTickSize'))

                    return {
                        'symbol': sym_info.get('symbol'),
                        'base_asset': base_asset,
                        'quote_asset': quote_asset,
                        'base_decimals': base_decimals,
                        'quote_decimals': quote_decimals,
                        'contract_val': sym_info.get('multiplier', None)
                    }

            raise Exception('Symbol was not found!')
        except RestError as e:
            # print(e, e.response)
            raise Exception(e.__str__())
        except Exception as e:
            raise Exception(e)


    def get_account_balance(self, symbol:str = None) -> AccountBalance:
        try:
            balances = {}

            if self.account_type == 'S':
                api = self.rest_service.get_account_service().get_account_api()
                account_list_req = (GetSpotAccountListReqBuilder().build())
                request = api.get_spot_account_list(account_list_req).to_dict()
                data = request.get('common_response')
                symbols = data.get('data', [])

                for balance in symbols:
                    if balance.get('type') == 'trade':
                        if symbol and balance['currency'] not in symbol:
                            continue
                        balances[balance['currency']] = {
                            'available': float(balance['available']),
                            'locked': float(balance['holds'])
                        }

            else:
                api = self.rest_service.get_account_service().get_account_api()

                acc_request = GetFuturesAccountReqBuilder().set_currency('USDT').build()
                request = api.get_futures_account(acc_request).to_dict()

                data = request.get('common_response')
                balance = data.get('data', {})

                balances[balance['currency']] = {
                    'available': float(balance['marginBalance']),
                    'locked': float(balance['accountEquity'])
                }

            return balances
        
        except RestError as e:
            raise Exception(e.__str__())
        except Exception as e:
            raise Exception(e)


    def open_trade(self, symbol, side, quantity, custom_id='', oc=False) -> OpenTrade:     
        try:

            sys_info = self.get_exchange_info(symbol)
            print(sys_info)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            order_symbol = sys_info.get('symbol')

            # order = self.get_order_info(order_symbol, '683b2bf64121360007cd1721')
            # raise Exception(order)

            adjusted_quantity =  self.adjust_trade_quantity(sys_info, side, quantity)

            print("Adjusted quantity:", adjusted_quantity)

            order_id = None

            if self.account_type == 'S':
                add_order_req = (
                    AddOrderReqBuilder()
                    .set_symbol(order_symbol)
                    .set_size(adjusted_quantity)
                    .set_side(str.lower(side))
                    .set_type('market')
                    .build()
                )

                api = self.rest_service.get_spot_service().get_order_api()
                request = api.add_order(add_order_req).to_dict()
                data = request.get('common_response')

                if data.get('code') == "200000":
                    order_id = data.get('data', {}).get('orderId')

            else:

                clientOid = f'{side}-{custom_id}-{int(time.time())}'
                add_order_req = (
                    AddFutureOrderReqBuilder()
                    .set_client_oid(clientOid)
                    .set_symbol(order_symbol)
                    .set_side(str.lower(side))
                    .set_size(math.ceil(float(adjusted_quantity)))
                    .set_type('market')
                    .set_reduce_only(oc)
                    .set_leverage(3)
                    .set_margin_mode('ISOLATED')
                    .build()
                )

                api = self.rest_service.get_futures_service().get_order_api()
                request = api.add_order(add_order_req).to_dict()
                data = request.get('common_response')

                if data.get('code') == "200000":
                    order_id = data.get('data', {}).get('orderId')

            if order_id:
                
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
                        'qty': adjusted_quantity,
                        'currency': currency_asset,
                    }
        
        except RestError as e:
            raise Exception(e.__str__())
        except Exception as e:
            raise Exception(e)

    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        """Close a trade."""
        opposite_side = "sell" if side.lower() == "buy" else "buy"

        return self.open_trade(symbol, opposite_side, quantity, oc=True)

    def get_order_info(self, symbol, order_id) -> OrderInfo:
        try:
            time.sleep(2)
            if self.account_type == 'S':

                order_req = (
                    GetTradeHistoryReqBuilder()
                    .set_symbol(symbol)
                    .set_order_id(order_id)
                    .build()
                )

                api = self.rest_service.get_spot_service().get_order_api()
                request = api.get_trade_history(order_req).to_dict()

                data = request.get('common_response', {})
                trades = data.get('data', {}).get('items', [])

                trade = next((item for item in trades if item.get('orderId') == order_id), None)

                # print(trade)

                if not trade:
                    order_req = (
                        GetOrderByOrderIdReqBuilder()
                        .set_symbol(symbol)
                        .set_order_id(order_id)
                        .build()
                    )

                    request = api.get_order_by_order_id(order_req).to_dict()

                    data = request.get('common_response', {})
                    trade = data.get('data', {})
                    # print(trade)


                if trade:
                    price_str = trade.get('price')

                    fees = trade.get('fee', 0)
                    fees = self.calculate_fees(symbol, price_str, fees, trade.get('feeCurrency'))
                    
                    r = {
                        'order_id': str(trade.get('orderId') or trade.get('id')),
                        'symbol': str(trade.get('symbol')),
                        'volume': str(trade.get('size')),
                        'side': str(trade.get('side')),
                        
                        'time': self.convert_timestamp(trade.get('createdAt')),
                        'price': str(price_str),

                        'profit': str(trade.get('profit', None)),

                        'fees': str(abs(fees)),

                        'additional_info': {
                            'fee': str(trade.get('fee')),
                            'feeCurrency': str(trade.get('feeCurrency')),
                            'feeRate': str(trade.get('feeRate')),
                        }
                    }

                    return r 
                
            else:

                order_req = (
                    GetFutureTradeHistoryReqBuilder()
                    .set_symbol(symbol)
                    .set_order_id(order_id)
                    .build()
                )

                api = self.rest_service.get_futures_service().get_order_api()
                request = api.get_trade_history(order_req).to_dict()

                data = request.get('common_response', {})
                trades = data.get('data', {}).get('items', [])
                
                trade = next((item for item in trades if item.get('orderId') == order_id), None)

                # print(trades)
                # print(trade)

                if trade:
                    price_str = trade.get('price')

                    fees = trade.get('fee', 0)
                    fees = self.calculate_fees(symbol, price_str, fees, trade.get('feeCurrency'))
                    
                    r = {
                        'order_id': str(trade.get('orderId') or trade.get('id')),
                        'symbol': str(trade.get('symbol')),
                        'volume': str(trade.get('size')),
                        'side': str(trade.get('side')),
                        
                        'time': self.convert_timestamp(trade.get('createdAt')),
                        'price': str(price_str),

                        'profit': str(trade.get('profit', None)),

                        'fees': str(abs(fees)),

                        'currency': trade.get('settleCurrency'),

                        'additional_info': {
                            'fee': str(trade.get('fee')),
                            'feeCurrency': str(trade.get('feeCurrency')),
                            'tradeId': str(trade.get('tradeId')),
                        }
                    }

                    # print(r)

                    return r 

            return None
        except RestError as e:
            print('Error getting trade info ', e.__str__())
            raise Exception(e.__str__())
        except Exception as e:
            raise Exception(e)
        
    
    def get_current_price(self, symbol):
        try:
            if self.account_type == 'S':
                symbol_req = GetTickerReqBuilder().set_symbol(symbol).build()
                request = self.rest_service.get_spot_service().get_market_api()

                response = request.get_ticker(symbol_req).to_dict()
                response = response.get('common_response')

                sym_info = response.get('data', {})
                # print(sym_info, type(sym_info), sym_info)
                if sym_info:
                    return float(sym_info.get('price'))
            else:
                symbol_req = GetTickerReqBuilder().set_symbol(symbol).build()
                request = self.rest_service.get_futures_service().get_market_api()
                response = request.get_ticker(symbol_req).to_dict()

                response = response.get('common_response')
                sym_info = response.get('data', {})
                
                if sym_info:
                    return float(sym_info.get('price'))

            raise Exception('Symbol was not found!')
        except RestError as e:
            # print(e, e.response)
            raise Exception(e.__str__())
        except Exception as e:
            raise Exception(e)


    def get_trading_pairs(self):
        try:
            symbols = []

            if self.account_type == 'S':
                req = GetAllSymbolsReqBuilder().build()
                request = self.rest_service.get_spot_service().get_market_api().get_all_symbols(req).to_dict()
                data = request.get('common_response')
                symbols_data = data.get('data', [])

                for sym in symbols_data:
                    symbols.append(sym.get('symbol'))
            else:
                request = self.rest_service.get_futures_service().get_market_api().get_all_symbols().to_dict()
                data = request.get('common_response')
                symbols_data = data.get('data', [])

                for sym in symbols_data:
                    symbols.append(sym.get('symbol'))

            return symbols
        except RestError as e:
            raise Exception(e.__str__())
        except Exception as e:
            raise Exception(e)
        
    def get_history_candles(self, symbol, interval, limit = 500):
        kucoin_intervals = {
            '1m': ('1min', 1),
            '3m': ('3min', 3),
            '5m': ('5min', 5),
            '15m': ('15min', 15),
            '30m': ('30min', 30),
            '45m': ('45min', 45),
            '1h': ('1hour', 60),
            '2h': ('2hour', 120),
            '4h': ('4hour', 240),
            '6h': ('6hour', 360),
            '8h': ('8hour', 480),
            '12h': ('12hour', 720),
            '1d': ('1day', 1440),
            '1W': ('1week', 10080),
            '1M': ('1month', 43200)
        }
        granularity = kucoin_intervals.get(interval, ('5min', 5))

        end_time = int(datetime.now(tz=timezone.utc).timestamp())
        start_time = end_time - (limit * int(granularity[1]) * 60)

        try:
            if self.account_type == 'S':
                req = GetKlinesReqBuilder().set_symbol(symbol).set_type(granularity[0]).set_start_at(start_time).set_end_at(end_time).build()
                request = self.rest_service.get_spot_service().get_market_api()

                response = request.get_klines(req).to_dict()
                response = response.get('common_response')

                data = response.get('data', [])
                candles = []

                for candle in data:
                    candles.append({
                        "time": self.convert_timestamp(int(candle[0]) * 1000),
                        "open": float(candle[1]),  # open
                        "high": float(candle[3]),  # high
                        "low": float(candle[4]),    # low
                        "close": float(candle[2]),  # close
                        "volume": float(candle[5])  # volume
                    })
                return candles

            else:
                req = GetFutureKlinesReqBuilder().set_symbol(symbol).set_granularity(granularity[1]).set_from_(start_time * 1000).set_to(end_time * 1000).build()
                request = self.rest_service.get_futures_service().get_market_api()
                response = request.get_klines(req).to_dict()

                response = response.get('common_response')
                data = response.get('data', [])
                
                candles = []

                for candle in data:
                    candles.append({
                        "time": self.convert_timestamp(int(candle[0]) * 1000),
                        "open": float(candle[1]),  # open
                        "high": float(candle[2]),  # high
                        "low": float(candle[3]),    # low
                        "close": float(candle[4]),  # close
                        "volume": float(candle[5])  # volume
                    })
                return candles
        except RestError as e:
            # print(e, e.response)
            raise Exception(e.__str__())
        except Exception as e:
            raise Exception(e)
        
    def get_order_book(self, symbol, limit = 100):
        try:
            if self.account_type == 'S':
                req = GetPartOrderBookReqBuilder().set_symbol(symbol).set_size('100').build()
                request = self.rest_service.get_spot_service().get_market_api()

                response = request.get_part_order_book(req).to_dict()
                response = response.get('common_response')

                data = response.get('data', {})
                    
                order_book = {
                    'bids': [{"price":float(b[0]), "qty":float(b[1])} for b in data.get('bids', [])],
                    'asks': [{"price":float(b[0]), "qty":float(b[1])} for b in data.get('asks', [])],
                    'time': self.convert_timestamp(data.get('time'))
                }

                return order_book
            else:
                req = GetFuturePartOrderBookReqBuilder().set_symbol(symbol).set_size('100').build()
                request = self.rest_service.get_futures_service().get_market_api()
                response = request.get_part_order_book(req).to_dict()

                response = response.get('common_response')
                data = response.get('data', {})
                
                order_book = {
                    'bids': [{"price":float(b[0]), "qty":float(b[1])} for b in data.get('bids', [])],
                    'asks': [{"price":float(b[0]), "qty":float(b[1])} for b in data.get('asks', [])],
                    'time': self.convert_timestamp(data.get('time'))
                }

                return order_book
            
        except RestError as e:
            # print(e, e.response)
            raise Exception(e.__str__())
        except Exception as e:
            raise Exception(e)