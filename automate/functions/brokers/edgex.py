from edgex_sdk import Client, OrderSide

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

class EdgexClient(CryptoBrokerClient):
    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        super().__init__(account, api_key, api_secret, passphrase, account_type, current_trade)

        base_url="https://pro.edgex.exchange"
        # base_url="https://testnet.edgex.exchange" testnet

        self.client = Client(base_url=base_url, account_id=api_key, stark_private_key=api_secret)


    @staticmethod
    def check_credentials(api_key, api_secret, account_type='S'):

        client = EdgexClient(api_key=api_key, api_secret=api_secret, account_type=account_type).client
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
        try:
            print('getting account balance')
            assets = await self.client.get_account_asset()
            print('assets', assets)
            return assets
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}
    
    def get_trading_pairs(self):
        pass
    
    def get_history_candles(self, symbol, interval, limit = 500):
        pass
    
    def get_order_book(self, symbol, limit = 100):
        pass

    async def get_contract_id(self, symbol):
        try:
            metadata = await self.client.get_metadata()
            print(metadata)
            contracts = metadata.get("data", {}).get("contractList", [])
            for contract in contracts:
                print(f"ID: {contract['contractId']} - {contract['contractName']}")
                if contract['contractName'] == symbol:
                    return contract['contractId']
        
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}