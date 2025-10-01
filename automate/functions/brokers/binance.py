from binance.spot import Spot
from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures
from binance.error import ClientError

from automate.functions.brokers.types import *
from automate.functions.brokers.broker import CryptoBrokerClient


class BinanceClient(CryptoBrokerClient):
    def __init__(self, account=None, api_key=None, api_secret=None, account_type="S", current_trade=None):
        super().__init__(account=account, api_key=api_key, api_secret=api_secret, account_type=account_type, current_trade=current_trade)

        if self.account_type == "S":  # Spot
            self.client = Spot(api_key=self.api_key, api_secret=self.api_secret)
        elif self.account_type == "U":  # USDM
            self.client = UMFutures(key=self.api_key, secret=self.api_secret)
        elif self.account_type == "C":  # COINM
            self.client = CMFutures(key=self.api_key, secret=self.api_secret)
        else:
            raise ValueError("Invalid trade type specified. Choose 'spot', 'usdm', or 'coinm'.")

    @staticmethod
    def check_credentials(api_key, api_secret, account_type="S"):
        try:
            client = BinanceClient(api_key=api_key, api_secret=api_secret, account_type=account_type).client
            account = client.account()

            if account:
                return {'message': "API credentials are valid.", "valid": True}
            else:
                return {'message': "API credentials are invalid.", "valid": False}
        
        except ClientError as e:
            return {"error": e.error_message}
        except Exception as e:
            print("ClientError:", e)
            return {"error": str(e)}

    def get_exchange_info(self, symbol) -> ExchangeInfo:
        try:
            symbol = self.adjust_symbol_name(symbol)
            if self.account_type == "S":
                response = self.client.exchange_info(symbol=symbol)
            else:
                response = self.client.exchange_info()

            if isinstance(response, list):
                data_list = response
            else:
                data_list = response.get('symbols', [])
            
            target = symbol.upper()
            for item in data_list:
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
            
            raise Exception("Symbol not found")
        
        except Exception as e:
            raise Exception(e)

            
    def get_account_balance(self, symbol: str = None) -> AccountBalance:
        try:
            trade_type = self.account_type
            balances = {}

            if trade_type == "S":  # Spot
                account_info = self.client.account()
                for balance in account_info['balances']:
                    if symbol and balance['asset'] not in symbol.upper():
                        continue
                    balances[balance['asset']] = {
                        'available': float(balance['free']),
                        'locked': float(balance['locked'])
                    }
            elif trade_type in ["U", "C"]:  # USDM or COINM Futures
                
                account_info = self.client.account()
                for balance in account_info['assets']:
                    if symbol and balance['asset'] not in symbol.upper():
                        continue
                    balances[balance['asset']] = {
                        'available': float(balance['availableBalance']),
                        'locked': float(balance['maxWithdrawAmount']) - float(balance['availableBalance'])
                    }
            else:
                raise ValueError("Invalid trade type. Use 'spot', 'usdm', or 'coinm'.")

            return balances
        
        except ClientError as e:
            raise ValueError(e.error_message)
        except Exception as e:
            raise ValueError(str(e))

       
    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None, oc = False) -> OpenTrade:
        try:
            trade_type = self.account_type
            sys_info = self.get_exchange_info(symbol)
            # print(sys_info)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity =  self.adjust_trade_quantity(sys_info, side, quantity)

            print("Adjusted quantity:", adjusted_quantity)
            if float(adjusted_quantity) <= 0:
                raise ValueError("Insufficient balance for the trade.")

            order_params = {
                "symbol": order_symbol,
                "side": str.upper(side),
                "type": "MARKET",
                "quantity": adjusted_quantity,
            }

            if self.account_type != "S":
                try:
                    self.client.change_position_mode(dualSidePosition=True)
                except ClientError as e:
                    print("Error changing position mode:", str(e.error_message))

                order_params['positionSide'] = 'LONG' if side.upper() == 'BUY' else 'SHORT'
                if oc:
                    order_params['positionSide'] = 'LONG' if side.upper() == 'SELL' else 'SHORT'

            response = self.client.new_order(**order_params)
            
            if trade_type == "C":
                currency_asset = sys_info.get('base_asset')
            
            order_id = response["orderId"]

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
                    'symbol': symbol,
                    "side": side.upper(),
                    'qty': order_details.get('volume', adjusted_quantity),
                    'price': order_details.get('price', '0'),
                    'time': order_details.get('time', ''),
                    'fees': order_details.get('fees', ''),
                    'currency':  order_details.get('currency') if order_details.get('currency') not in (None, 'None') else currency_asset,

                    'trade_details': trade_details
                }
            else:
                return {
                    'message': f"Trade opened with order ID {response.get('orderId')}.",
                    'order_id': response.get('orderId'),
                    'symbol': symbol,
                    "side": side.upper(),
                    'price': (response['fills'][0].get('price') if response.get('fills') and len(response['fills']) > 0 else response.get('price', '')),
                    # 'fees': response['fills'][0]['commission'],
                    'qty': (
                        response.get('executedQty')
                        if float(response.get('executedQty', 0)) > 0
                        else adjusted_quantity
                    ),
                    'currency': currency_asset,
                }

        
        except ClientError as e:
            raise ValueError(e.error_message)
        except Exception as e:
            raise ValueError(str(e))
        
    def close_trade(self, symbol: str, side: str, quantity: float) -> CloseTrade:
        """Close a trade on Binance."""
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        return self.open_trade(symbol, t_side, quantity, oc=True)
        
 
    def get_order_info(self, symbol, order_id) -> OrderInfo:

        try:
            trade_type = self.account_type

            params = {
                "symbol": symbol,
                "orderId": order_id
            }

            if trade_type == "S":
                response = self.client.my_trades(**params)
            else:
                response = self.client.get_account_trades(**params)
            
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

            # print("Trade details:", trade)
            
            if trade:
                fees = float(trade.get('commission'))

                if trade_type != "C":
                    fees = self.calculate_fees(symbol, trade.get('price', '0'), fees, trade.get('commissionAsset'))

                
                r = {
                    'order_id': str(trade.get('orderId')),
                    'symbol': str(trade.get('symbol')),
                    'volume': str(trade.get('qty')),
                    'side': str(trade.get('side')),
                    
                    'time': self.convert_timestamp(trade.get('time')),
                    'price': str(trade.get('price')),

                    'profit': str(trade.get('realizedPnl')),
                    'fees': str(fees),

                    'currency': str(trade.get('marginAsset')),

                    'additional_info': {
                        'commission': str(trade.get('commission')),
                        'commissionAsset': str(trade.get('commissionAsset')),
                    },
                }

                return r 
            
            return None

        except ClientError as e:
            raise ValueError(e.error_message)
        except Exception as e:
            raise ValueError(str(e))

    # ------------------------------------------------------------------------------------------------------------------------
    # methods for market data
    # ------------------------------------------------------------------------------------------------------------------------
        
    def get_trading_pairs(self) -> list:
        try:
            if self.account_type == "S":
                response = self.client.exchange_info()
            else:
                response = self.client.exchange_info()


            symbols = []
            data_list = response.get('symbols', [])
            
            for item in data_list:
                status = item.get('status', '')
                contractStatus = item.get('contractStatus', '')

                if status != 'TRADING' and contractStatus != 'TRADING':
                    continue
                
                base_asset = item.get('baseAsset')
                quote_asset = item.get('quoteAsset')
                symbol = item.get('symbol')

                symbols.append({
                    'symbol': symbol,
                    'base_asset': base_asset,
                    'quote_asset': quote_asset,
                })

            return symbols
        
        except ClientError as e:
            raise ValueError(e.error_message)
        except Exception as e:
            raise ValueError(str(e))
        
    def get_history_candles(self, symbol: str, interval: str, limit: int = 500):
        try:
            sys_info = self.get_exchange_info(symbol)
            if not sys_info:
                raise Exception('Symbol was not found!')

            order_symbol = sys_info.get('symbol')

            response = self.client.klines(symbol=order_symbol, interval=interval, limit=limit)
            
            ohlcv_data = []
            for entry in response:
                ohlcv = {
                    'timestamp': self.convert_timestamp(entry[0]),
                    'open': float(entry[1]),
                    'high': float(entry[2]),
                    'low': float(entry[3]),
                    'close': float(entry[4]),
                    'volume': float(entry[5]),
                }
                ohlcv_data.append(ohlcv)

            return ohlcv_data
        
        except ClientError as e:
            raise ValueError(e.error_message)
        except Exception as e:
            raise ValueError(str(e))
        
    def get_order_book(self, symbol: str, limit: int = 100) :
        try:
            sys_info = self.get_exchange_info(symbol)
            if not sys_info:
                raise Exception('Symbol was not found!')

            order_symbol = sys_info.get('symbol')

            response = self.client.depth(symbol=order_symbol, limit=limit)
            
            bids = [{"price":float(price), "qty":float(qty)} for price, qty in response['bids']]
            asks = [{"price":float(price), "qty":float(qty)} for price, qty in response['asks']]

            return {
                'lastUpdateId': response['lastUpdateId'],
                'bids': bids,
                'asks': asks
            }
        
        except ClientError as e:
            raise ValueError(e.error_message)
        except Exception as e:
            raise ValueError(str(e))
        
    def get_current_price(self, symbol: str) -> float:
        try:
            sys_info = self.get_exchange_info(symbol)
            if not sys_info:
                raise Exception('Symbol was not found!')

            order_symbol = sys_info.get('symbol')

            response = self.client.ticker_price(symbol=order_symbol)

            # If the response is a list/tuple, use the first item
            if isinstance(response, (list, tuple)):
                if not response:
                    raise Exception('Empty price response')
                response = response[0]

            # Normalize possible response shapes
            price = None
            if isinstance(response, dict):
                for key in ('price', 'lastPrice', 'askPrice'):
                    if key in response and response[key] not in (None, ''):
                        price = response[key]
                        break
            else:
                # response might be a plain number or string
                price = response

            if price is None:
                raise Exception(f"Could not find price in response: {response}")

            return float(price)
        
        except ClientError as e:
            raise ValueError(e.error_message)
        except Exception as e:
            raise ValueError(str(e))

