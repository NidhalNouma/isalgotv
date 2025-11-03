import lighter
import eth_account


class LighterClient():
    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        pass

    async def main(self):
        BASE_URL = "https://testnet.zklighter.elliot.ai"
        L1_ADDRESS = "0xF807731Cf34EBEEFF7D7437174906a162360D53F"
        ACCOUNT_INDEX = 65


        client = lighter.ApiClient(configuration=lighter.Configuration(host=BASE_URL))
        account_instance = lighter.AccountApi(client)


        acc = await account_instance.account(by='l1_address', value=L1_ADDRESS)

        print(acc)

        apis = await account_instance.apikeys(account_index=ACCOUNT_INDEX, api_key_index=1)
        print(apis)

        order_instance = lighter.OrderApi(client)



    @staticmethod
    def check_credentials(api_key, api_secret, account_type='S'):
        client = LighterClient(api_key=api_key, api_secret=api_secret, account_type=account_type).client
        pass

    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None, oc = False):
        pass

    async def close_trade(self, trade_id: str):
        pass

    async def get_account_balance(self, symbol=None):
        pass

    def get_trading_pairs(self):
        pass