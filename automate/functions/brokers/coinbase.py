from coinbase.rest import RESTClient

from .broker import CryptoBrokerClient
from .types import *

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

            print(accounts)
            
            return {'message': "API credentials are valid.", 'valid': True}
        
            return {'error': 'API credentials are not valid.', 'valid': False}
        except Exception as e:
            return {'error': str(e), 'valid': False}
        
    def get_exchange_info(self, symbol) -> ExchangeInfo:
        pass
        
    def get_account_balance(self) -> AccountBalance:
        pass
        
    def open_trade(self) -> OpenTrade:
        pass
        
    def close_trade(self) -> CloseTrade:
        pass

    def get_order_info(self, symbol, order_id) -> OrderInfo:
        pass