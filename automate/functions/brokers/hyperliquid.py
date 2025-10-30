from hyperliquid.info import Info
from hyperliquid.utils import constants

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

class HyperliquidClient(CryptoBrokerClient):
    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        super().__init__(account, api_key, api_secret, passphrase, account_type, current_trade)

        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        user_state = info.user_state(api_key)
        print(user_state)


    @staticmethod
    def check_credentials(api_key, api_secret, account_type='S'):

        client = HyperliquidClient(api_key=api_key, api_secret=api_secret, account_type=account_type).client
        pass
    
    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None, oc = False):
        pass
    
    def close_trade(self, symbol: str, side: str, quantity: float):
        pass
    
    def get_order_info(self, symbol, order_id):
        pass
    


    def get_exchange_info(self, symbol):
        pass
    
    
    def get_current_price(self, symbol):
        pass
        
    async def get_account_balance(self, symbol=None):
        pass
    
    def get_trading_pairs(self):
        pass
    
    def get_history_candles(self, symbol, interval, limit = 500):
        pass
    
    def get_order_book(self, symbol, limit = 100):
        pass