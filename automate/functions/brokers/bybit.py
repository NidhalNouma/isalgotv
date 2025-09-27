from automate.functions.brokers.types import *
from automate.functions.brokers.broker import CryptoBrokerClient

from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError, FailedRequestError

# Derivatives of the CryptoBrokerClient for Bybit works only with USDT

class BybitClient(CryptoBrokerClient):
    BYBIT_API_URL = 'https://api.bybit.com/v5'

    def __init__(self, account=None, api_key=None, api_secret=None, account_type="S", current_trade=None):
        super().__init__(account=account, api_key=api_key, api_secret=api_secret, account_type=account_type, current_trade=current_trade)

        self.session = HTTP(
                testnet=False,
                api_key=self.api_key,
                api_secret=self.api_secret,
            )

        if self.account_type == "S":
            self.category = 'spot'
        else:
            self.category = 'linear'

    @staticmethod
    def check_credentials(api_key, api_secret, account_type="S"):
        """Check the validity of the Bybit API credentials without instantiating."""
        try:
            client = BybitClient(api_key=api_key, api_secret=api_secret, account_type=account_type)
            response = client.session.get_account_info()
            if response.get('retCode') != 0:
                return {'error': response.get('retMsg'), 'valid': False}
            return {'message': "API credentials are valid.", 'valid': True}
        except (InvalidRequestError, FailedRequestError) as e:
            # return {'error': "API credentials are not valid.", 'valid': False}
            return {'error': str(e.message), 'valid': False}
        except Exception as e:
            return {'error': str(e), 'valid': False}
        
        
    def get_exchange_info(self, symbol) -> ExchangeInfo:
        try:
            response = self.session.get_instruments_info(category=self.category, symbol=symbol)

            if response['retCode'] != 0:
                raise Exception(response['retMsg'])

            data = response['result']['list'][0]
            
            if self.category == 'spot':
                b_precison = data['lotSizeFilter']['basePrecision']
                q_precison = data['lotSizeFilter']['quotePrecision']

                quote_decimals = self.get_decimals_from_step(q_precison)
                base_decimals   = self.get_decimals_from_step(b_precison)
            else:
                precison = data['lotSizeFilter']['qtyStep']

                quote_decimals = self.get_decimals_from_step(precison)
                base_decimals   = self.get_decimals_from_step(precison)

            r ={
                'symbol': data['symbol'],
                'base_asset': data['baseCoin'],
                'quote_asset': data['quoteCoin'],
                'base_decimals': base_decimals,
                'quote_decimals': quote_decimals
            }

            return r

        except (InvalidRequestError, FailedRequestError) as e:
            raise Exception(e.message)
        except Exception as e:
            raise Exception(str(e))
        

    def get_account_balance(self, symbol: str = None) -> AccountBalance:
        """Get the balance of a specific asset on Bybit."""
        try:
            response = self.session.get_wallet_balance(
                accountType='UNIFIED',
            )
            # print('coin', response)
            if response['retCode'] != 0:
                raise Exception(response['retMsg'])
            
            b = {}
            for balance in response['result']['list'][0]['coin']:
                # if balance['coin'] == coin:
                if symbol and balance['coin'] not in symbol:
                    continue

                b[balance['coin']] = balance['walletBalance']
                b[balance['coin']] = {
                    'available': balance['walletBalance'],
                    'locked': balance['availableToBorrow'] 
                }
            return b
        
        except (InvalidRequestError, FailedRequestError) as e:
            raise Exception(e.message)
        except Exception as e:
            raise Exception(str(e))

    def open_trade(self, symbol, side, quantity, custom_id = '', oc = False) -> OpenTrade:
        """Place a market order on Bybit."""
        try:
                
            sys_info = self.get_exchange_info(symbol)

            # print("System info:", sys_info, quantity)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            base_asset = sys_info.get('base_asset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity = self.adjust_trade_quantity(sys_info, side, quantity)

            print("Adjusted quantity:", adjusted_quantity)
            if float(adjusted_quantity) <= 0:
                raise ValueError("Insufficient balance for the trade.")

            if self.account_type != "S":
                try:
                    self.session.switch_position_mode(
                        category=self.category,
                        symbol=order_symbol,
                        mode=3
                    )
                except (InvalidRequestError, FailedRequestError) as e:
                    print(f"Error switching position mode: {e.message}")

            if oc:
                response = self.session.place_order(
                    category=self.category,
                    symbol=order_symbol,
                    side=side.capitalize(),
                    positionIdx=2 if side.lower() == 'buy' else 1,
                    orderType="Market",
                    qty=adjusted_quantity,
                    marketUnit='baseCoin',
                    time_in_force='IOC',
                    reduceOnly=True,
                )
            else:
                response = self.session.place_order(
                    category=self.category,
                    symbol=order_symbol,
                    side=side.capitalize(),
                    positionIdx=1 if side.lower() == 'buy' else 2,
                    orderType="Market",
                    qty=adjusted_quantity,
                    marketUnit='baseCoin',
                    time_in_force='IOC'
                )

            # print('r', response)
            if response['retCode'] != 0:
                raise Exception(response['retMsg'])
            
            order_id = response['result']['orderId']

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
                    'price': order_details.get('price', '0') or self.get_exchange_price(order_symbol),
                    'time': order_details.get('time', ''),
                    'fees': order_details.get('fees', ''),
                    'currency': order_details.get('currency') if order_details.get('currency') not in (None, "None") else currency_asset,

                    'trade_details': trade_details
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
                }
            
        except (InvalidRequestError, FailedRequestError) as e:
            return {'error': str(e.message)}
        except Exception as e:
            return {'error': str(e)}

    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        """Close a trade on Bybit."""
        opposite_side = "sell" if side.lower() == "buy" else "buy"

        return self.open_trade(symbol, opposite_side, quantity, oc=True)


    def get_order_info(self, symbol, order_id) -> OrderInfo:
        try:

            response = self.session.get_executions(category=self.category, symbol=symbol, orderId=order_id)
            response = response.get('result', {}).get('list', [])
            
            if response is None:
                raise ValueError("No data found in response")
            
            if isinstance(response, list):
                if len(response) > 1:
                    total_qty = sum(float(t.get('execQty', 0)) for t in response)
                    total_commission = sum(float(t.get('execFee', 0)) for t in response)
                    
                    trade = response[-1]
                    trade['execFee'] = str(total_commission)
                    trade['execQty'] = str(total_qty)

                else:
                    trade = response[0]
            else:
                trade = response

            if trade:
                # print('Trade details:', trade)
                # Fallback to 'price' if 'priceAvg' is missing or falsy
                price_str = trade.get('execPrice') or trade.get('orderPrice', None)

                # Normalize fee detail, which may be a dict or a list of dicts
                fees = trade.get('execFee', 0)
                fees = self.calculate_fees(symbol, price_str, fees, trade.get('feeCurrency'))
                
                r = {
                    'order_id': str(trade.get('orderId')),
                    'symbol': str(trade.get('symbol')),
                    'volume': str(trade.get('execQty') or trade.get('orderQty')),
                    'side': str(trade.get('side')),
                    
                    'time': self.convert_timestamp(trade.get('execTime')),
                    'price': str(price_str),

                    'profit': str(trade.get('profit', None)),

                    'fees': str(abs(fees)),

                    'additional_info': {
                        'execFee': str(trade.get('execFee')),
                        'feeCurrency': str(trade.get('feeCurrency')),
                        'feeRate': str(trade.get('feeRate')),
                    }
                }

                return r 
            
            return None

        except Exception as e:
            print('error getting order details: ', str(e))
            return None

    # ------------------------------------------------------------------------------------------------------------------------
    # methods for market data
    # ------------------------------------------------------------------------------------------------------------------------

    def get_trading_pairs(self) -> List[str]:
        """Get a list of available trading pairs on Bybit."""
        try:
            response = self.session.get_instruments_info(category=self.category)

            if response['retCode'] != 0:
                raise Exception(response['retMsg'])

            symbols = [item['symbol'] for item in response['result']['list']]
            return symbols

        except (InvalidRequestError, FailedRequestError) as e:
            raise Exception(e.message)
        except Exception as e:
            raise Exception(str(e))        


    def get_exchange_price(self, symbol):
        """Get the current price of a symbol on Bybit."""
        try:
            response = self.session.get_tickers(category=self.category, symbol=symbol)

            if response['retCode'] != 0:
                raise Exception(response['retMsg'])

            data = response['result']['list'][0]
            return data['lastPrice']

        except (InvalidRequestError, FailedRequestError) as e:
            raise Exception(e.message)
        except Exception as e:
            raise Exception(str(e))

    def get_order_book(self, symbol, limit=50):
        """Get the order book for a symbol on Bybit."""
        try:
            response = self.session.get_orderbook(
                category=self.category,
                symbol=symbol,
                limit=limit
            )

            if response['retCode'] != 0:
                raise Exception(response['retMsg'])

            data = response['result']
            return data

        except (InvalidRequestError, FailedRequestError) as e:
            raise Exception(e.message)
        except Exception as e:
            raise Exception(str(e))
        
    def get_history_candles(self, symbol, interval, limit=100):
        """Get historical candlestick data for a symbol on Bybit."""
        try:

            valid_intervals = ["1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d","3d","1w","1M"]
            if interval not in valid_intervals:
                raise ValueError(f"Invalid interval: {interval}. Valid intervals are: {', '.join(valid_intervals)}")
            # mapping numeric/short tokens <-> Bybit interval strings
            to_bybit = {
                "1": "1m", "3": "3m", "5": "5m", "15": "15m", "30": "30m",
                "60": "1h", "120": "2h", "240": "4h", "360": "6h", "480": "8h", "720": "12h",
                "D": "1d", "W": "1w", "M": "1M"
            }
            # reverse mapping: if user passed a Bybit interval (e.g. "1m"), convert to token (e.g. "1")
            from_bybit = {v: k for k, v in to_bybit.items()}

            # Accept either token ("1", "60", "D") or Bybit format ("1m", "1h", "1d").
            # If user passed a Bybit interval, set `interval` to its token (reversed mapping).
            # Use `api_interval` for the actual call to Bybit (always a Bybit-format string).
            if interval in from_bybit:
                interval = from_bybit[interval]      # user-visible reversed mapping (e.g. "1m" -> "1")
            api_interval = to_bybit.get(interval, interval)

            if api_interval not in valid_intervals:
                raise ValueError(f"Invalid interval: {interval}. Valid intervals are: {', '.join(valid_intervals)}")
 

            response = self.session.get_kline(
                category=self.category,
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            if response['retCode'] != 0:
                raise Exception(response['retMsg'])

            data = response['result']['list']
            candles = []
            for item in data:
                candles.append({
                    'timestamp': self.convert_timestamp(item[0]),
                    'open': item[1],
                    'high': item[2],
                    'low': item[3],
                    'close': item[4],
                    'volume': item[5]
                })
            return candles

        except (InvalidRequestError, FailedRequestError) as e:
            raise Exception(e.message)
        except Exception as e:
            raise Exception(str(e))
        