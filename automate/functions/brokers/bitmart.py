
from bitmart.api_spot import APISpot
from bitmart.api_contract import APIContract
from bitmart.lib import cloud_exceptions

from .broker import CryptoBrokerClient
from .types import *

class BitmartClient(CryptoBrokerClient):


    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        super().__init__(account=account, api_key=api_key, api_secret=api_secret, passphrase=passphrase, account_type=account_type, current_trade=current_trade)

        if self.account_type == "S":
            self.API = APISpot(self.api_key, self.api_secret, self.passphrase, timeout=(3, 10))
        else:
            self.API = APIContract(self.api_key, self.api_secret, self.passphrase, timeout=(3, 10))


    @staticmethod
    def check_credentials(api_key, api_secret, passphrase, account_type="S"):
        """Check the validity of the Bitmart API credentials without instantiating."""
        try:
            client = BitmartClient(api_key=api_key, api_secret=api_secret, passphrase=passphrase, account_type=account_type)
            response = client.API.get_wallet()

            if response[0]['code'] != 1000:
                return {'error': response.get('message'), 'valid': False}
            
            return {'message': "API credentials are valid.", 'valid': True}
        except cloud_exceptions.APIException as apiException:
            # print("Error[HTTP<>200]:", apiException.response)
            return {'error': str(apiException.response), 'valid': False}
        except Exception as e:
            return {'error': str(e), 'valid': False}
        
    
    def get_exchange_info(self, symbol) -> ExchangeInfo:

        try:
            if self.account_type == 'S':
                response = self.API.get_symbol_detail()

                if response[0].get('code') != 1000:
                    raise Exception(response.message)
                else:
                    symbols = response[0].get('data', {}).get('symbols', [])

                    target = symbol.upper()
                    for item in symbols:
                        inst = item.get('symbol', '')
                        if inst.replace('_', '').upper() == target or inst == target:

                            print(item)
                            base_asset = item.get('base_currency')
                            quote_asset = item.get('quote_currency')
                            base_decimals = self.get_decimals_from_step(item.get('base_min_size'))
                            quote_decimals = self.get_decimals_from_step(item.get('min_buy_amount'))

                            return {
                                'symbol': item.get('symbol'),
                                'base_asset': base_asset,
                                'quote_asset': quote_asset,
                                'base_decimals': base_decimals,
                                'quote_decimals': quote_decimals,
                            }
            else:
                response = self.API.get_assets_detail()


            
            return None

        except cloud_exceptions.APIException as apiException:
            raise Exception(apiException.response)
        except Exception as e:
            raise Exception(str(e))


    def get_account_balance(self) -> AccountBalance:
        pass


    def open_trade(self, symbol, side, quantity, oc = False) -> OpenTrade:
        try:

            sys_info = self.get_exchange_info(symbol)
            print(sys_info)
 
        except cloud_exceptions.APIException as apiException:
            raise Exception(apiException.response)
        except Exception as e:
            raise Exception(str(e))


    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        opposite_side = "sell" if side.lower() == "buy" else "buy"

        return self.open_trade(symbol, opposite_side, quantity, oc=True)
    

    def get_order_info(self, symbol, order_id) -> OrderInfo:
        pass