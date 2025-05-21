import time
import hmac
import hashlib
import requests
import json

from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP

from .broker import BrokerClient

class BybitClient(BrokerClient):
    BYBIT_API_URL = 'https://api.bybit.com/v5'

    def __init__(self, account=None, api_key=None, api_secret=None, account_type="S", current_trade=None):

        if account is not None:
            self.api_key = account.apiKey
            self.api_secret = account.secretKey
            self.account_type = getattr(account, 'accountType', None) or getattr(account, 'type', None)
        else:
            self.api_key = api_key
            self.api_secret = api_secret
            self.account_type = account_type
        self.current_trade = current_trade

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
        
        
    def get_exchange_info(self, symbol):
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
                'baseCoin': data['baseCoin'],
                'quoteCoin': data['quoteCoin'],
                'baseDecimals': base_decimals,
                'quoteDecimals': quote_decimals
            }

            return r

        except Exception as e:
            raise Exception(e)
        

    def get_account_balance(self):
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
            return b
        except Exception as e:
            raise Exception(e)
        
    def adjust_trade_quantity(self, symbol_info, side, quote_order_qty):
        try:
            base_asset = symbol_info.get('baseCoin')
            quote_asset = symbol_info.get('quoteCoin')

            account_balace = self.get_account_balance()
            print("Account balance:", account_balace)

            base_balance = account_balace.get(base_asset, 0)
            quote_balance = account_balace.get(quote_asset, 0)

            base_decimals = symbol_info.get('baseDecimals') 
            quote_decimals = symbol_info.get('quoteDecimals') 

            print("Base asset:", base_asset, base_decimals)
            print("Quote asset:", quote_asset, quote_decimals)

            print("Base balance:", base_balance)
            print("Quote balance:", quote_balance)

            try:
                precision = int(base_decimals)
            except (TypeError, ValueError):
                precision = 8  # fallback precision
            quant = Decimal(1).scaleb(-precision)  


            if self.account_type == "S":  # Spot

                if side.upper() == "BUY":
                    if float(quote_balance) <= 0:
                        raise ValueError("Insufficient quote balance.")

                    qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                    return format(qty_dec, f'.{precision}f')
                
                elif side.upper() == "SELL":
                    if float(base_balance) <= 0:
                        raise ValueError("Insufficient base balance.")
                    elif float(base_balance) < float(quote_order_qty):
                        # Format quantity to max base_decimals and return as string
                        qty_dec = Decimal(str(base_balance)).quantize(quant, rounding=ROUND_DOWN)
                        return format(qty_dec, f'.{precision}f')
                    # Format quantity to max base_decimals and return as string
                    qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                    return format(qty_dec, f'.{precision}f')
                
                return quote_order_qty
            else:  # Futures

                qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                return format(qty_dec, f'.{precision}f')

        except Exception as e:
            raise ValueError(str(e))

        

    def open_trade(self, symbol, side, quantity, additional_params={}):
        """Place a market order on Bybit."""
        try:
                
            sys_info = self.get_exchange_info(symbol)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quoteCoin')
            base_asset = sys_info.get('baseCoin')
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

    def close_trade(self, symbol, side, quantity):
        """Close a trade on Bybit."""
        opposite_side = "sell" if side.lower() == "buy" else "buy"

        additional_params = {
            'reduceOnly': 'true',
            'closeOnTrigger': 'true',
        }
        return self.open_trade(symbol, opposite_side, quantity, additional_params)


    def get_order_info(self, symbol, order_id):
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

                sym_info = self.get_exchange_info(symbol)
                # Fallback to 'price' if 'priceAvg' is missing or falsy
                price_str = trade.get('execPrice') or trade.get('orderPrice', '0')
                price_usdt = Decimal(str(price_str))

                # Normalize fee detail, which may be a dict or a list of dicts
                fees = trade.get('execFee', 0)
                sym_info = self.get_exchange_info(symbol)

                try:
                    fees = Decimal(str(fees))
                    if str(trade.get('feeCurrency')) == sym_info.get('baseCoin'):
                        fees = fees * price_usdt
                except (InvalidOperation, ValueError):
                    pass


                dt_aware = self.convert_timestamp(trade.get('execTime'))
                
                r = {
                    'order_id': str(trade.get('orderId')),
                    'symbol': str(trade.get('symbol')),
                    'volume': str(trade.get('execQty') or trade.get('orderQty')),
                    'side': str(trade.get('side')),
                    
                    'time': dt_aware,
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

