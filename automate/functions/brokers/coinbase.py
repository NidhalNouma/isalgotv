from coinbase.rest import RESTClient
from datetime import datetime, timezone

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

class CoinbaseClinet(CryptoBrokerClient):

    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        super().__init__(account=account, api_key=api_key, api_secret=api_secret, passphrase=passphrase, account_type=account_type, current_trade=current_trade)

        self.client = RESTClient(api_key=self.api_key, api_secret=self.api_secret)


    @staticmethod
    def check_credentials(api_key, api_secret, account_type="S"):
        """Check the validity of the Bitmart API credentials without instantiating."""
        try:
            client = CoinbaseClinet(api_key=api_key, api_secret=api_secret, account_type=account_type).client

            accounts = client.get_accounts()

            # print(accounts)
            
            return {'message': "API credentials are valid.", 'valid': True}
        
            return {'error': 'API credentials are not valid.', 'valid': False}
        except Exception as e:
            return {'error': str(e), 'valid': False}
        
    def get_exchange_info(self, symbol) -> ExchangeInfo:
        try:
            # response = self.client.get_products(product_type='FUTURE')
            # products = response.products
            # for p in products:
            #     print(p.product_id)
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
                    'base_asset': product.future_product_details.get('contract_code'),
                    'quote_asset': product.quote_currency_id,
                    'base_decimals': self.get_decimals_from_step(product.base_increment),
                    'quote_decimals': self.get_decimals_from_step(product.quote_increment),
                }
        except Exception as e:
            raise Exception(str(e))
        
    def get_account_balance(self) -> AccountBalance:
        try:
            balances = {}

            response = self.client.get_accounts()
            accounts = response.accounts

            for account in accounts:
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
                response = self.client.market_order_buy(client_order_id=None, product_id=symbol, base_size=quantity)
            elif str.lower(side) == 'sell':            
                response = self.client.market_order_sell(client_order_id=None, product_id=symbol, base_size=quantity)
            else:
                raise Exception('Order type is not supported.')
            
            result = response.to_dict()
            # print(result)

            if result.get('success') == False:
                raise Exception(result.get('error_response', {}).get('message', 'Error occured.'))

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
                    'currency': order_details.get('currency') if order_details.get('currency') is not None else currency_asset,

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
            raise Exception(str(e))
        
    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        try:
            opposite_side = "sell" if side.lower() == "buy" else "buy"

            if self.account_type == 'S':
                return self.open_trade(symbol=symbol, side=opposite_side, quantity=quantity)

            response = self.client.close_position(client_order_id=None, product_id=symbol, size=quantity)

 
            result = response.to_dict()
            # print(result)

            if result.get('success') == False:
                raise Exception(result.get('error_response', {}).get('message', 'Error occured.'))

            order_id = result.get('success_response', {}).get('order_id')



        except Exception as e:
            raise Exception(str(e))

    def get_order_info(self, symbol, order_id) -> OrderInfo:
        try:
            response = self.client.get_order(order_id=order_id)
            trade = response.to_dict().get('order')
            print(trade)
            
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

                    'additional_info': {
                        'client_order_id': str(trade.get('client_order_id')),
                        'outstanding_hold_amount': str(trade.get('outstanding_hold_amount')),
                    }
                }

                return r 


        except Exception as e:
            raise Exception(str(e))