from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, ClosePositionRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.requests import CryptoLatestQuoteRequest, StockLatestQuoteRequest, OptionLatestQuoteRequest, CryptoBarsRequest, StockBarsRequest, OptionBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta, timezone

from automate.functions.brokers.broker import BrokerClient

class AlpacaClient(BrokerClient):
    def __init__(self, account=None, username=None, password=None, server=None, type='L', current_trade=None):
        self.symbols_cache = {}
        self.current_trade = current_trade

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
            return market_order
        except Exception as e:
            print('Error opening trade:', str(e))
            return {'error': str(e)}
        
    def close_trade(self, symbol, side, quantity):
        try:
            close_pos_req = ClosePositionRequest(qty=quantity)
            close_market = self.client.close_position(symbol_or_asset_id=symbol, close_options=close_pos_req)

        except Exception as e:
            print('Error closing trade:', str(e))
            return {'error': str(e)}

    def get_order_info(self, symbol, order_id):
        try:
            order = self.client.get_order_by_id(order_id=order_id)
            return order

        
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

    def get_account_balance(self):
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

    def get_symbol_info(self, symbol):
        try:
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

    def market_and_account_data(self, symbol, intervals, limit = 500):
        try:
            symbol_info = self.get_symbol_info(symbol=symbol)

        except Exception as e:
            print('')


        