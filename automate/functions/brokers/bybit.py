import time
import hmac
import hashlib
import requests

from .types import *

from .broker import CryptoBrokerClient

class BybitClient(CryptoBrokerClient):
    BYBIT_API_URL = 'https://api.bybit.com/v5'

    def __init__(self, account=None, api_key=None, api_secret=None, account_type="S", current_trade=None):
        super().__init__(account=account, api_key=api_key, api_secret=api_secret, account_type=account_type, current_trade=current_trade)

        if self.account_type == "S":
            self.category = 'spot'
        else:
            self.category = 'linear'

    def create_bybit_signature(self, params):
        """Create the signature for a Bybit API request."""
        sorted_params = sorted(params.items())
        query_string = '&'.join(f"{key}={value}" for key, value in sorted_params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'), 
            query_string.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
        return signature

    def send_bybit_request(self, method, endpoint, params):
        """Send a request to the Bybit API."""
        params['api_key'] = self.api_key
        params['timestamp'] = str(int(time.time() * 1000))
        params['sign'] = self.create_bybit_signature(params)
        
        url = f"{self.BYBIT_API_URL}{endpoint}"
        if method.upper() == 'GET':
            response = requests.get(url, params=params)
        else:
            response = requests.post(url, json=params)
        return response.json()

    @staticmethod
    def check_credentials(api_key, api_secret, account_type="S"):
        """Check the validity of the Bybit API credentials without instantiating."""
        try:
            client = BybitClient(api_key=api_key, api_secret=api_secret, account_type=account_type)
            params = {'accountType': 'UNIFIED'}
            endpoint = '/account/wallet-balance'
            response = client.send_bybit_request('GET', endpoint, params)
            if response.get('retCode') != 0:
                return {'error': response.get('retMsg'), 'valid': False}
            return {'message': "API credentials are valid.", 'valid': True}
        except Exception as e:
            return {'error': str(e), 'valid': False}
        
        
    def get_exchange_info(self, symbol) -> ExchangeInfo:
        try:
            params = {
                'symbol': symbol,
                'category': self.category,
            }
            
            response = self.send_bybit_request('GET', '/market/instruments-info', params)

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

        except Exception as e:
            raise Exception(e)
        

    def get_account_balance(self) -> AccountBalance:
        """Get the balance of a specific asset on Bybit."""
        try:
            params = {
                'accountType': 'UNIFIED',
                # 'coin': coin
            }
            endpoint = '/account/wallet-balance'
            response = self.send_bybit_request('GET', endpoint, params)
            # print('coin', response)
            if response['retCode'] != 0:
                raise Exception(response['retMsg'])
            
            b = {}
            for balance in response['result']['list'][0]['coin']:
                # if balance['coin'] == coin:
                b[balance['coin']] = balance['walletBalance']
                b[balance['coin']] = {
                    'available': balance['walletBalance'],
                    'locked': balance['walletBalance'] - balance['availableBalance']
                }
            return b
        except Exception as e:
            raise Exception(e)

    def open_trade(self, symbol, side, quantity, additional_params={}) -> OpenTrade:
        """Place a market order on Bybit."""
        try:
                
            sys_info = self.get_exchange_info(symbol)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            base_asset = sys_info.get('base_asset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity = self.adjust_trade_quantity(sys_info, side, float(quantity))

            print("Adjusted quantity:", adjusted_quantity)
            if float(adjusted_quantity) <= 0:
                raise ValueError("Insufficient balance for the trade.")

            endpoint = '/order/create'
            params = {
                'symbol': order_symbol,
                'side': side.capitalize(),
                'order_type': 'Market',
                'qty': str(adjusted_quantity),
                
                'category': self.category,

                'marketUnit': 'baseCoin',
                'time_in_force': 'IOC',
                **additional_params
            }
                
            response = self.send_bybit_request('POST', endpoint, params)

            # print(response)
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
                    'price': order_details.get('price', '0'),
                    'time': order_details.get('time', ''),
                    'fees': order_details.get('fees', ''),
                    'currency': currency_asset,

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
        except Exception as e:
            return {'error': str(e)}

    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        """Close a trade on Bybit."""
        opposite_side = "sell" if side.lower() == "buy" else "buy"

        additional_params = {
            'reduceOnly': 'true',
            'closeOnTrigger': 'true',
        }
        return self.open_trade(symbol, opposite_side, quantity, additional_params)


    def get_order_info(self, symbol, order_id) -> OrderInfo:
        try:
            endpoint = '/execution/list'

            params = {
                'category': self.category,
                'symbol': symbol,
                'orderId': order_id,
            }

            response = self.send_bybit_request('GET', endpoint, params)
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
                # Fallback to 'price' if 'priceAvg' is missing or falsy
                price_str = trade.get('execPrice') or trade.get('orderPrice', '0')

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

