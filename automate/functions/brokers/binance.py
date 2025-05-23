from binance.spot import Spot
from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures
from binance.error import ClientError

from .types import *
from .broker import CryptoBrokerClient

class BinanceClient(CryptoBrokerClient):
    def __init__(self, account=None, api_key=None, api_secret=None, account_type="S", current_trade=None):
        super().__init__(account, api_key, api_secret, account_type, current_trade)

        if account_type == "S":  # Spot
            self.client = Spot(api_key, api_secret)
        elif account_type == "U":  # USDM
            self.client = UMFutures(api_key, api_secret)
        elif account_type == "C":  # COINM
            self.client = CMFutures(api_key, api_secret)
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
            return {"error": str(e)}

    def get_exchange_info(self, symbol) -> ExchangeInfo:
        try:
            response = self.client.exchange_info(symbol)
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
                        'baseAsset': base_asset,
                        'quoteAsset': quote_asset,
                        'base_decimals': base_decimals,
                        'quote_decimals': quote_decimals,
                    }
            
            return None
        
        except Exception as e:
            raise Exception(e)

            
    def get_account_balance(self, asset: str) ->AccountBalance:
        try:
            trade_type = self.account_type
            balances = {}

            if trade_type == "S":  # Spot
                account_info = self.client.account()
                for balance in account_info['balances']:
                    balances[balance['asset']] = float(balance['free'])
            elif trade_type in ["U", "C"]:  # USDM or COINM Futures
                
                account_info = self.client.account()
                for balance in account_info['assets']:
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

       
    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None) -> OpenTrade:
        try:
            trade_type = self.account_type
            sys_info = self.get_exchange_info(symbol)
            # print(sys_info)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity =  self.adjust_trade_quantity(sys_info, side, float(quantity))

            print("Adjusted quantity:", adjusted_quantity)
            if float(adjusted_quantity) <= 0:
                raise ValueError("Insufficient balance for the trade.")

            order_params = {
                "symbol": symbol,
                "side": str.upper(side),
                "type": "MARKET",
                "quantity": adjusted_quantity,
                # "reduceOnly": "true",
            }

            response = self.client.new_order(**order_params)
            
            if trade_type == "C":
                currency_asset = sys_info.get('baseAsset')
            
            order_id = response["orderId"]
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
                    'currency': currency_asset,
                }
            else:
                return {
                    'message': f"Trade opened with order ID {response.get('orderId')}.",
                    'order_id': response.get('orderId'),
                    'symbol': response.get('symbol', symbol),
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
        try:
            t_side = "SELL" if side.upper() == "BUY" else "BUY"
            trade_type = self.account_type

            sys_info = self.get_exchange_info(symbol)
            # print(sys_info)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            quote_asset = sys_info.get('quoteAsset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity =  self.adjust_trade_quantity(sys_info, t_side, float(quantity))
            print("Adjusted quantity:", adjusted_quantity)

            order_params = {
                "symbol": symbol,
                "side": str.upper(t_side),
                "type": "MARKET",
                "quantity": adjusted_quantity,
                "reduceOnly": "true",
            }

            response = self.client.new_order(**order_params)

            if response.get('msg') is not None:
                raise Exception(response.get('msg'))

            return {
                'message': f"Trade closed for order ID {response.get('orderId')}.",
                "symbol": symbol,

                "id": response.get('orderId'),
                "closed_order_id": response["orderId"],
                "side": t_side.upper(),
                # Use executedQty if present and > 0, else use adjusted_quantity
                'qty': (
                    response.get('executedQty')
                    if float(response.get('executedQty', 0)) > 0
                    else adjusted_quantity
                ),
                'price': (response['fills'][0].get('price') if response.get('fills') and len(response['fills']) > 0 else response.get('price', '')),
            }
        
        except ClientError as e:
            raise ValueError(e.error_message)
        except Exception as e:
            raise ValueError(str(e))
 
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

                    'profit': str(trade.get('realizedPnl', None)),

                    'fees': str(fees),

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
            