# Trading is in One way only hedging is not supported
# Offers Stocks, Funds, Crypto, Indices, and options

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, ClosePositionRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.requests import CryptoLatestQuoteRequest, StockLatestQuoteRequest, OptionLatestQuoteRequest, CryptoBarsRequest, StockBarsRequest, OptionBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta, timezone

from automate.functions.brokers.broker import BrokerClient
from automate.functions.brokers.types import *
import time

class AlpacaClient(BrokerClient):
    def __init__(self, account=None, username=None, password=None, server=None, type='L', current_trade=None):
        self.symbols_cache = {}
        self.current_trade = current_trade
        self.account_currency = self.current_trade.currency if self.current_trade else None

        if account:
            self.api_key = account.username
            self.api_secret = account.password
            self.type = account.type
        else:
            self.api_key = username
            self.api_secret = password
            self.type = type
            
        self.client = TradingClient(self.api_key, self.api_secret, paper=True if self.type == 'D' else False)

    @staticmethod
    def check_credentials(username, password, type):
        try:
            client = AlpacaClient(username=username, password=password, type=type)
            account = client.get_account_info()
            if not account:
                raise Exception('Invalid credentials.')
            return {'valid': True, 'message': 'Credentials are valid.'}
        except Exception as e:
            print(f"Credential check failed: {e}")
            return {'valid': False, 'error': str(e)}

    def open_trade(self, symbol: str, side: str, quantity, custom_id = ''):
        try:
            symbol_info = self.get_symbol_info(symbol=symbol)

            if not symbol_info:
                raise Exception('Invalid symbol/asset.')

            req_side = None
            if side.lower() == 'buy':
                req_side = OrderSide.BUY
            elif side.lower() == 'sell':
                req_side = OrderSide.SELL
            else:
                raise Exception('Unsupported order side.')

            order_req = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=req_side,
                time_in_force=TimeInForce.IOC,
                client_order_id=custom_id
            )

            market_order = self.client.submit_order(order_data=order_req)
            end_exe = time.perf_counter()
            order_id = market_order.id

            order_info = self.get_order_info(symbol=symbol, order_id=order_id)
            return {**order_info, 'end_exe': end_exe}
        except Exception as e:
            print('Error opening trade:', str(e))
            return {'error': str(e)}
        
    def close_trade(self, symbol, side, quantity):
        try:
            close_pos_req = ClosePositionRequest(qty=str(quantity))
            close_market = self.client.close_position(symbol_or_asset_id=symbol, close_options=close_pos_req)
            end_exe = time.perf_counter()
            close_id = close_market.id

            return {
                'message': f"Trade closed for order ID {id}.", 
                "closed_order_id": close_id,
                'qty': close_market.qty,
                'end_exe': end_exe
            }

            # order_info = self.get_order_info(symbol, close_id)
            # return order_info

        except Exception as e:
            print('Error closing trade:', str(e))
            return {'error': str(e)}

    def get_order_info(self, symbol, order_id):
        try:
            order = self.retry_until_response(
                func=self.client.get_order_by_id,
                is_desired_response=lambda resp: resp is not None and resp.status == 'filled',
                kwargs={'order_id': order_id},
                max_attempts=4,
                delay_seconds=1,
            )
            
            if not order:
                raise Exception('Order NA.')
            if order.status != 'filled':
                raise Exception('Order not filled yet.')

            # print(order)
            
            order_data = OrderInfo(
                symbol=order.symbol,
                order_id=order.id,
                volume=order.filled_qty,
                side=order.side,
                time=order.filled_at,
                price=order.filled_avg_price,
                currency=self.currency,
                fees=0,
            )
            return order_data

        
        except Exception as e:
            raise Exception(e)

    def get_position(self, symbol, order_id):
        try:
            pos = self.client.get_open_position(symbol_or_asset_id=symbol)
            return pos

        except Exception as e:
            raise Exception(e)

    def get_account_info(self):
        try:
            account = self.client.get_account()
            return account
        except Exception as e:
            print(f"Error fetching account info: {e}")
            return None

    @property
    def currency(self):
        if self.account_currency:
            return self.account_currency
        account = self.get_account_info()
        if account:
            # cache the currency for future calls
            self.account_currency = getattr(account, 'currency', None)
            return self.account_currency
        # return None when account info is not available
        return None

    def get_account_balance(self, symbol: str = None):
        try:
            account = self.client.get_account()
            return {
                'balance': float(account.cash) + float(account.equity) - float(account.portfolio_value),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'equity': float(account.equity),
                'portfolio_value': float(account.portfolio_value)
            }
        except Exception as e:
            print(f"Error fetching account balance: {e}")
            return None

    def get_trading_pairs(self):
        try:
            assets = self.client.get_all_assets()
            trading_pairs = [asset.symbol for asset in assets if asset.tradable]
            return trading_pairs
        except Exception as e:
            print(f"Error fetching trading pairs: {e}")
            return []

    def get_symbol_info(self, symbol: str):
        try:
            symbol = symbol.upper()
            if symbol in self.symbols_cache:
                return self.symbols_cache[symbol]
            asset = self.client.get_asset(symbol)
            self.symbols_cache[symbol] = asset
            return asset
        except Exception as e:
            print(f"Error fetching exchange info for {symbol}: {e}")
            return None
        
    def get_current_price(self, symbol):
        try:
            # Determine asset type
            asset = self.get_symbol_info(symbol)
            if asset is None:
                return None

            if asset.asset_class == 'crypto':
                data_client = CryptoHistoricalDataClient()
                request_params = CryptoLatestQuoteRequest(symbol_or_symbols=[symbol])
                latest_quote = data_client.get_crypto_latest_quote(request_params)
            elif asset.asset_class == 'us_equity':
                data_client = StockHistoricalDataClient(api_key=self.api_key, secret_key=self.api_secret)
                request_params = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
                latest_quote = data_client.get_stock_latest_quote(request_params)
            elif asset.asset_class == 'option':
                data_client = OptionHistoricalDataClient(api_key=self.api_key, secret_key=self.api_secret)
                request_params = OptionLatestQuoteRequest(symbol_or_symbols=[symbol])
                latest_quote = data_client.get_option_latest_quote(request_params)
            else:
                print(f"Unsupported asset class for {symbol}: {asset.asset_class}")
                return None

            ask = latest_quote[symbol].ask_price  
            bid = latest_quote[symbol].bid_price

            return {
                'ask': ask,
                'bid': bid
            }
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {e}")
            return None

    def get_history_candles(self, symbol, timeframe, limit=100):
        try:
            al_timeframes = {
                '1m': (TimeFrame(1, TimeFrameUnit.Minute), 1),
                '5m': (TimeFrame(5, TimeFrameUnit.Minute), 5),
                '15m': (TimeFrame(15, TimeFrameUnit.Minute), 15),
                '30m': (TimeFrame(30, TimeFrameUnit.Minute), 30),
                '1h': (TimeFrame(1, TimeFrameUnit.Hour), 60),
                '4h': (TimeFrame(4, TimeFrameUnit.Hour), 240),
                '1d': (TimeFrame.Day, 1440),
                '1w': (TimeFrame.Week, 10080),
                '1M': (TimeFrame.Month, 43200),
            }
            _timeframe = al_timeframes.get(timeframe, None)
            if _timeframe is None:
                print(f"Unsupported timeframe: {timeframe}")
                return []

            # Determine asset type
            asset = self.get_symbol_info(symbol)
            if asset is None:
                return None

            start_time = datetime.now(timezone.utc) - timedelta(minutes=_timeframe[1] * limit)
            end_time = datetime.now(timezone.utc)

            print(f"Fetching candles for {symbol} from {start_time} to {end_time} with timeframe {timeframe}")

            if asset.asset_class == 'crypto':
                data_client = CryptoHistoricalDataClient()
                bar_request = CryptoBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=_timeframe[0],
                    start=datetime(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute, tzinfo=timezone.utc),
                    end=datetime(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute, tzinfo=timezone.utc)
                )
                bars = data_client.get_crypto_bars(bar_request)
            elif asset.asset_class == 'us_equity':
                data_client = StockHistoricalDataClient(api_key=self.api_key, secret_key=self.api_secret)
                bar_request = StockBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=_timeframe[0],
                    start=datetime(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute, tzinfo=timezone.utc),
                    end=datetime(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute, tzinfo=timezone.utc)
                )
                bars = data_client.get_stock_bars(bar_request)
            elif asset.asset_class == 'option':
                data_client = OptionHistoricalDataClient(api_key=self.api_key, secret_key=self.api_secret)
                bar_request = OptionBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=_timeframe[0],
                    start=start_time,
                    end=end_time,
                )
                bars = data_client.get_option_bars(bar_request)
            else:
                print(f"Unsupported asset class for {symbol}: {asset.asset_class}")
                return None

            bars = bars.dict().get(symbol, [])
            r_bars = [{
                'time': bar.get('timestamp'),
                'open': bar.get('open'),
                'high': bar.get('high'),
                'low': bar.get('low'),
                'close': bar.get('close'),
                'volume': bar.get('volume'),
            } for bar in bars]
            return r_bars
            
        except Exception as e:
            print(f"Error fetching historical candles for {symbol}: {e}")
            return []


    def market_and_account_data(self, symbol: str, intervals: List[str], limit: int = 500) -> dict:
        try:
            history_candles = {}
            
            try:
                symbol_info = self.get_symbol_info(symbol=symbol)
                symbol = symbol_info.symbol
            except Exception as e:
                symbol_info = {}
                print("Error fetching symbol info:", e)

            for intv in intervals:
                if intv not in ["1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d","3d","1w","1M"]:
                    raise ValueError(f"Invalid interval: {intv}")
                history_candles[intv] = self.get_history_candles(symbol, intv, limit=limit)

            try:
                account_balance = self.get_account_balance()
            except Exception as e:
                account_balance = {}
                print("Error fetching account balance:", e)

            try:
                price = self.get_current_price(symbol)
            except Exception as e:
                price = "NA"
                print("Error fetching price:", e)

            return {
                'history_candles': history_candles,
                'account_balance': account_balance,
                'symbol_info': symbol_info,
                'current_price': price,
            }
        
        except Exception as e:
            raise ValueError(str(e))


        