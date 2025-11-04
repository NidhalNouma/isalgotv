from datetime import datetime
import lighter
from lighter.models.req_get_trades import ReqGetTrades
from lighter.models.candlestick import Candlestick

import asyncio 
import eth_account


class LighterClient():
    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        pass

    async def main(self):
        BASE_URL = "https://testnet.zklighter.elliot.ai"
        L1_ADDRESS = "0xF807731Cf34EBEEFF7D7437174906a162360D53F"
        PRIVATE_KEY = "f77e0bf30b5674ae22d5ad9f029fc931970e76e98fc27923bb985cca9283a1d51c9e2b3bfa4a017b"
        PUBLIC_KEY = "d7c34f0a8a57fd47f1781d50ea231141f1816a9bda18e6514a6e20b24fecb36c1899338d62270124"
        API_KEY_INDEX = 0
        ACCOUNT_INDEX = 196


        b_client = lighter.ApiClient(configuration=lighter.Configuration(host=BASE_URL))
        account_instance = lighter.AccountApi(b_client)


        acc = await account_instance.account(by='l1_address', value=L1_ADDRESS)

        print(acc)

        apis = await account_instance.apikeys(account_index=ACCOUNT_INDEX, api_key_index=API_KEY_INDEX)
        print(apis)

        client = lighter.SignerClient(  
            url=BASE_URL,
            private_key=PRIVATE_KEY,
            account_index=ACCOUNT_INDEX,
            api_key_index=API_KEY_INDEX
        )
        
        err = client.check_client()
        if err is not None:
            print(f"CheckClient error: {err}")
            return

        auth, err = client.create_auth_token_with_expiry(
            lighter.SignerClient.DEFAULT_10_MIN_AUTH_EXPIRY
        )
        if err is not None:
            print(f"CreateAuthToken error: {err}")
            return
        
        print(f"Auth Token: {auth}")

        # tx, tx_hash, err = await client.create_order(
        #     market_index=0,
        #     client_order_index=123,
        #     base_amount=100,
        #     price=1,
        #     is_ask=True,
        #     order_type=lighter.SignerClient.ORDER_TYPE_MARKET,
        #     time_in_force=lighter.SignerClient.ORDER_TIME_IN_FORCE_IMMEDIATE_OR_CANCEL,
        #     reduce_only=False,
        #     order_expiry=0,
        #     trigger_price=0,
        # )
        # print(f"Create Order {tx=} {tx_hash=} {err=}")
        # if err is not None:
        #     raise Exception(err)

        from datetime import datetime
        from lighter.models.candlestick import Candlestick

        candlestick_instance = lighter.CandlestickApi(b_client)
        req_candles = await candlestick_instance.candlesticks(
            market_id=0,
            resolution='1h',
            start_timestamp=int(datetime.now().timestamp() - 60 * 60 * 24),
            end_timestamp=int(datetime.now().timestamp()),
            count_back=2,
        )
        candles = req_candles.candlesticks

        for candle in candles:
            print({
                "timestamp": candle.timestamp,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume0": candle.volume0,
                "volume1": candle.volume1
            })



        order_instance = lighter.OrderApi(b_client)

        req = await order_instance.trades(sort_by='trade_index', limit=10)

        print(req)

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