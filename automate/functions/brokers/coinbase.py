# Spot: Quantity is in base asset units. Account balance needs to have enough base and quote asset to trade in both directions.
# Perpetual and Futures: User needs to set the API portfolio to perpetual on the exchange platform. https://www.coinbase.com/settings/api
# Perpretual: Quantity is in base asset units. leverage is set to 20x. 

# Perpetual and Futures: Hedge mode is not supported.


from coinbase.rest import RESTClient, products
from datetime import datetime, timezone
import time

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *


class CoinbaseClient(CryptoBrokerClient):

    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        super().__init__(account=account, api_key=api_key, api_secret=api_secret, passphrase=passphrase, account_type=account_type, current_trade=current_trade)

        self.client = RESTClient(api_key=self.api_key, api_secret=self.api_secret)


    @staticmethod
    def check_credentials(api_key, api_secret, account_type="S"):
        """Check the validity of the Bitmart API credentials without instantiating."""
        try:
            client = CoinbaseClient(api_key=api_key, api_secret=api_secret, account_type=account_type).client

            accounts = client.get_accounts()

            # print(accounts)
            
            return {'message': "API credentials are valid.", 'valid': True}
        except Exception as e:
            return {'error': str(e), 'valid': False}

        
    def get_exchange_info(self, symbol) -> ExchangeInfo:
        try:
            symbol = self.adjust_symbol_name(symbol)

            product = self.client.get_product(symbol)

            # print(product)
            if self.account_type == 'S':
                return {
                    'symbol': product.product_id,
                    'base_asset': product.base_currency_id,
                    'quote_asset': product.quote_currency_id,
                    'base_decimals': self.get_decimals_from_step(product.base_increment),
                    'quote_decimals': self.get_decimals_from_step(product.quote_increment),
                }
            else:
                return {
                    'symbol': product.product_id,
                    'base_asset': product.future_product_details.get('contract_code') if product.future_product_details else product.base_currency_id,
                    'quote_asset': product.quote_currency_id,
                    'base_decimals': self.get_decimals_from_step(product.base_increment),
                    'quote_decimals': self.get_decimals_from_step(product.quote_increment),
                }
        except Exception as e:
            raise Exception(str(e))
        
    def get_account_balance(self, symbol:str = None) -> AccountBalance:
        try:
            balances = {}

            response = self.client.get_accounts()
            accounts = response.accounts

            for account in accounts:
                if symbol and account.currency not in symbol:
                    continue
                balances[account.currency] = {
                    'available': float(account.available_balance.get('value', 0)),
                    'locked': float(account.hold.get('value', 0))
                }

            return balances

        except Exception as e:
            raise Exception(str(e))
        
    def open_trade(self, symbol, side, quantity, custom_id = '') -> OpenTrade:
        try:
            sys_info = self.get_exchange_info(symbol)
            print(sys_info)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity =  self.adjust_trade_quantity(sys_info, side, quantity)

            print("Adjusted quantity:", adjusted_quantity)

            if str.lower(side) == 'buy':            
                response = self.client.market_order_buy(client_order_id=None, product_id=order_symbol, base_size=str(adjusted_quantity), leverage="20" if self.account_type != 'S' else "1")
            elif str.lower(side) == 'sell':            
                response = self.client.market_order_sell(client_order_id=None, product_id=order_symbol, base_size=str(adjusted_quantity), leverage="20" if self.account_type != 'S' else "1")
            else:
                raise Exception('Order type is not supported.')
            
            end_exe = time.perf_counter()
            result = response.to_dict()
            # print(response)

            if result.get('success') == False:
                error_msg = result.get('error_response', {}).get('message', 'Error occured.')
                if not error_msg:
                    error_msg = result.get('error_response', {}).get('preview_failure_reason', 'Error occured.')
                raise Exception(error_msg)

            order_id = result.get('success_response', {}).get('order_id')

            if not order_id:
                raise Exception('OrderId do not exisit.')
            
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
                    'currency': order_details.get('currency') if order_details.get('currency') not in (None, "None") else currency_asset,

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
            
        except Exception as e:
            raise Exception(str(e))
        
    def close_trade(self, symbol: str, side: str, quantity) -> CloseTrade:
        try:
            symbol = self.adjust_symbol_name(symbol)
            opposite_side = "sell" if side.upper()  in ("BUY", "B") else "buy"

            if self.account_type == 'S':
                return self.open_trade(symbol=symbol, side=opposite_side, quantity=quantity)

            symbol_info = self.get_exchange_info(symbol)
            if not symbol_info:
                raise Exception('Symbol was not found!')
            
            order_symbol = symbol_info.get('symbol')

            quantity = self.adjust_trade_quantity(symbol_info, opposite_side, quantity)
            # print("Closing trade:", symbol, opposite_side, quantity)

            response = self.client.close_position(client_order_id=None, product_id=order_symbol, size=str(quantity))
            # print(response)

            end_exe = time.perf_counter()

 
            result = response.to_dict()

            if result.get('success') == False:
                raise Exception(result.get('error_response', {}).get('message', 'Error occured.'))

            order_id = result.get('success_response', {}).get('order_id')

            
            if not self.current_trade:
                order_details = self.get_order_info(symbol, str(order_id))
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
                    'qty': order_details.get('volume', quantity),
                    'price': order_details.get('price', '0'),
                    'time': order_details.get('time', ''),
                    'fees': order_details.get('fees', ''),
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
                    'qty': quantity,
                    "end_exe": end_exe
                }
            

        except Exception as e:
            raise Exception(str(e))

    def get_order_info(self, symbol, order_id) -> OrderInfo:
        try:
            response = self.client.get_order(order_id=order_id)
            trade = response.to_dict().get('order')

            # print(trade)
            
            if trade:
                dt = datetime.strptime(trade.get('created_time'), "%Y-%m-%dT%H:%M:%S.%fZ")
                time = dt.replace(tzinfo=timezone.utc)
                r = {
                    'order_id': str(trade.get('order_id')),
                    'symbol': str(trade.get('product_id')),
                    'volume': str(trade.get('filled_size')),
                    'side': str(trade.get('side')),
                    
                    'time': time,
                    'price': str(trade.get('average_filled_price')),

                    'profit': str(trade.get('realised_profit', None)),

                    'fees': str(trade.get('total_fees')),

                    'currency': str(trade.get('fill_fees_currency')),

                    'additional_info': {
                        'client_order_id': str(trade.get('client_order_id')),
                        'outstanding_hold_amount': str(trade.get('outstanding_hold_amount')),
                    }
                }

                return r 


        except Exception as e:
            raise Exception(str(e))


    def get_current_price(self, symbol) -> float:
        try:
            response = self.client.get_public_product(product_id=symbol)
            ticker = response.to_dict()
            return float(ticker.get('price', 0))
        except Exception as e:
            raise Exception(str(e))

    def get_trading_pairs(self):
        try:
            response = self.client.get_products(
                product_type="UNKNOWN_PRODUCT_TYPE" if self.account_type == 'S' else 'FUTURE',
                contract_expiry_type="UNKNOWN_CONTRACT_EXPIRY_TYPE" if self.account_type == 'F' else 'PERPETUAL'
            )

            products = response.products

            symbols = []
            for product in products:
                symbols.append(product.product_id)

            return symbols

        except Exception as e:
            raise Exception(str(e))
        
    def get_history_candles(self, symbol, interval, limit = 500):
        try:
            if limit > 350:
                limit = 350
            mapping = {
                '1m': ('ONE_MINUTE', 60),
                '5m': ('FIVE_MINUTE', 300),
                '15m': ('FIFTEEN_MINUTE', 900),
                '30m': ('THIRTY_MINUTE', 1800),
                '1h': ('ONE_HOUR', 3600),
                '2h': ('TWO_HOUR', 7200),
                '4h': ('FOUR_HOUR', 14400),
                '6h': ('SIX_HOUR', 21600),
                '1d': ('ONE_DAY', 86400),
            }
            granularity = mapping.get(interval, ('FIVE_MINUTE', 300))

            end_time = int(datetime.now(tz=timezone.utc).timestamp())
            start_time = end_time - (limit * int(granularity[1]))

            # print("Start time:", datetime.fromtimestamp(start_time, tz=timezone.utc))

            response = self.client.get_public_candles(product_id=symbol, start=str(start_time), end=str(end_time), granularity=granularity[0], limit=limit)
            candles = response.candles

            # print(candles)

            ohlc = []
            for candle in candles:
                ohlc.append({
                    "time": self.convert_timestamp(int(candle.start) * 1000),
                    # "timestamp": int(entry[0]) * 1000,
                    "open": float(candle.open),  # open
                    "high": float(candle.high),  # high
                    "low": float(candle.low),    # low
                    "close": float(candle.close),  # close
                    "volume": float(candle.volume)  # volume
                })
            
            # Sort by time ascending
            ohlc.sort(key=lambda x: x['time'])

            return ohlc

        except Exception as e:
            raise Exception(str(e))
        

    def get_order_book(self, symbol, limit = 100):
        try:
            response = self.client.get_product_book(product_id=symbol, limit=limit)
            order_book = response.to_dict().get('pricebook', {})

            # print(order_book)

            bids = order_book.get('bids', [])
            asks =  order_book.get('asks', [])

            return {
                'bids': bids,
                'asks': asks
            }

        except Exception as e:
            raise Exception(str(e))