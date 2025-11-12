# Perps: Quantity is in base asset units. 
# Hedge trading is not supported.

from http import client
import time 
from apexomni.constants import APEX_OMNI_HTTP_MAIN, APEX_HTTP_MAIN, NETWORKID_MAIN
from apexomni.http_private_sign import HttpPrivateSign
from apexomni.http_public import HttpPublic

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *


class ApexClient(CryptoBrokerClient):
    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        
        self.coins = {}
        self.symbols = {}
        super().__init__(account=account, api_key=api_key, api_secret=api_secret, passphrase=passphrase , account_type=account_type, current_trade=current_trade)


        try:
            _passphrase, _zk_seed = self.passphrase.split('||')
            self.passphrase = _passphrase

            self.public_client = HttpPublic(APEX_OMNI_HTTP_MAIN)
            
            self.private_client = HttpPrivateSign(
                    endpoint=APEX_HTTP_MAIN,
                    network_id=NETWORKID_MAIN,
                    zk_seeds=_zk_seed,
                    api_key_credentials={'key': self.api_key, 'secret': self.api_secret, 'passphrase': self.passphrase},
                )  
            
            configs = self.private_client.configs_v3()
            accountData = self.private_client.get_account_v3()

        except Exception as e:
            print(f"Error initializing ApexClient: {e}")
            raise e


    @staticmethod
    def check_credentials(api_key, api_secret, passphrase, account_type='S'):
        try:
            cl = ApexClient(api_key=api_key, api_secret=api_secret, passphrase=passphrase, account_type=account_type)
            private_Client = cl.private_client

            userRes = private_Client.get_user_v3()

            if 'code' in userRes:
                raise Exception(f"Error {userRes['code']}: {userRes.get('message', 'Unknown error')}")
            return {'message': "API credentials are valid.", "valid": True}
        except Exception as e:
            print(f"An error occurred during credential check: {e}")
            return {'error': "API credentials are invalid.", "valid": False}


    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None, oc = False):
        try:
            trade_type = self.account_type
            sys_info = self.get_exchange_info(symbol)
            # print(sys_info)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            order_symbol = sys_info.get('symbol')

            adjusted_quantity =  self.adjust_trade_quantity(sys_info, side, quantity)
            adjusted_quantity =  quantity

            print("Adjusted quantity:", adjusted_quantity)
            if float(adjusted_quantity) <= 0:
                raise ValueError("Insufficient balance for the trade.")

            currentTime = time.time()

            price = self.get_current_price(symbol)
        
            order_params = {
                "symbol": order_symbol,
                "side": str.upper(side),
                "type": "MARKET",
                "size": adjusted_quantity,
                "timestampSeconds": currentTime,
                "price": price,
            }

            if self.account_type != "S":
                # try:
                #     self.client.change_position_mode(dualSidePosition=True)
                # except Exception as e:
                #     print("Error changing position mode:", str(e))

                if oc:
                    order_params["reduceOnly"] = True

            response = self.private_client.create_order_v3(**order_params)
            response = response.get('data', {})
            end_exe = time.perf_counter()

            if 'code' in response:
                raise Exception(f"Error {response['code']}: {response.get('message', 'Unknown error')}")

            order_id = response.get('orderId')
            if not order_id:
                raise Exception("Order ID not found in response.")

            if not self.current_trade:
                order_details = self.get_order_info(order_symbol, order_id)
                trade_details = None 
            else:
                order_details = self.get_final_trade_details(self.current_trade, order_id)
                trade_details = order_details

            if order_details:
                return {
                    'message': f"Trade opened with order ID {order_id}.",
                    'order_id': order_id,
                    'symbol': order_symbol,
                    "side": side.upper(),
                    'qty': order_details.get('volume', adjusted_quantity),
                    'price': order_details.get('price', '0'),
                    'time': order_details.get('time', ''),
                    'fees': order_details.get('fees', ''),
                    'currency':  order_details.get('currency') if order_details.get('currency') not in (None, 'None') else currency_asset,

                    'trade_details': trade_details,
                    "end_exe": end_exe
                }
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': order_id,
                'closed_order_id': order_id if oc else '',
                'symbol': response.get('symbol', order_symbol),

                'price': response.get('price', price),
                # 'fees': response['fills'][0]['commission'],
                'qty': response.get('size', adjusted_quantity),
                'time': self.convert_timestamp(response.get('createdAt', int(currentTime * 1000))),
                'currency': currency_asset,
                "end_exe": end_exe
            }
            
        except Exception as e:
            print(f"An error occurred while opening trade: {e}")
            raise e

    def close_trade(self, symbol: str, side: str, quantity: float):
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        return self.open_trade(symbol, t_side, quantity, oc=True)

    def get_order_info(self, symbol, order_id):
        try:
            info = self.get_exchange_info(symbol)
            if info:
                symbol = info.get('symbol', symbol)
            # print("Fetching order info for order ID:", order_id, symbol)  # --- IGNORE ---
            response = self.private_client.fills_v3(symbol=symbol, order_type='MARKET')


            if 'code' in response:
                raise Exception(f"Error {response['code']}: {response.get('message', 'Unknown error')}")

            orders = response.get('data', {}).get('orders', [])

            for order in orders:
                if str(order.get('orderId')) == str(order_id):
                    r = {
                        'order_id': order.get('orderId'),
                        'symbol': order.get('symbol'),
                        'price': order.get('price'),
                        'volume': order.get('size'),
                        'time': self.convert_timestamp(order.get('createdAt')),
                        'status': order.get('status'),
                        'side': order.get('side'),
                        'fees': order.get('fee'),
                    }

                    return r
            return None

        except client.RemoteDisconnected as e:
            print(f"RemoteDisconnected error: {e}")
            return None
        except Exception as e:
            print(f"Error getting order info: {e}")
            return None

    def get_exchange_info(self, symbol):
        try:
            if symbol in self.symbols:
                return self.symbols[symbol]
            request = self.public_client.configs_v3()

            data = request['data'].get('contractConfig', {}).get('perpetualContract', [])

            for item in data:
                if item['crossSymbolName'] == symbol:
                    # return item
                    r = {
                        'symbol': item['symbol'],
                        'base_asset': item['baseTokenId'],
                        'quote_asset': item['settleAssetId'],
                        'base_decimals': self.get_decimals_from_step(item['stepSize']),
                        'quote_decimals': item['indexPriceDecimals'],
                        'min_order_size': float(item['minOrderSize']),
                        'max_order_size': float(item['maxOrderSize']),
                    }
                    self.symbols[symbol] = r
                    return r
            return None

        except client.RemoteDisconnected as e:
            print(f"RemoteDisconnected error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_current_price(self, symbol):
        try:
            symbol = symbol.replace("-", "")
            ticker = self.public_client.ticker_v3(symbol=symbol)
            for item in ticker['data']:
                if item['symbol'] == symbol:
                    return float(item['lastPrice'])
            return None
        except client.RemoteDisconnected as e:
            print(f"RemoteDisconnected error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_account_balance(self, symbol=None):
        try:
            data = self.private_client.get_account_v3()
            if self.account_type == "S":
                wallet = data.get('spotWallets', {})
                balance = {}

                for asset in wallet:
                    coin = self.get_coin_by_token_id(asset['tokenId'])

                    balance[coin['token']] = {'available': float(asset['balance'])}

                return balance
            
            elif self.account_type == "P":
                wallet = data.get('contractWallets', {})
                balances = {}

                for asset in wallet:
                    balances[asset['token']] = { 'available': float(asset['balance'])}
                return balances
            else:
                raise Exception("Invalid account type. Use 'S' for Spot or 'P' for Perpetual.")
        except client.RemoteDisconnected as e:
            print(f"RemoteDisconnected error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_trading_pairs(self):
        try:
            exchange_info = self.public_client.configs_v3()
            trading_pairs = [item['crossSymbolName'] for item in exchange_info['data'].get('contractConfig', {}).get('perpetualContract', [])]
            return trading_pairs
        except client.RemoteDisconnected as e:
            print(f"RemoteDisconnected error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_history_candles(self, symbol, interval, limit = 500):
        try:
            symbol = symbol.replace("-", "")
            if limit > 200:
                limit = 200

            interval = interval.replace("m", "").replace("d", "D").replace("w", "W").replace("M", "M")

            if "h" in interval:
                hours = int(interval.replace("h", ""))
                interval = str(hours * 60)

            request = self.public_client.klines_v3(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            candles = []
            data = request['data'].get(symbol, [])
            for candle in data:
                candles.append({
                    'timestamp': self.convert_timestamp(candle['t']),
                    'open': float(candle['o']),
                    'high': float(candle['h']),
                    'low': float(candle['l']),
                    'close': float(candle['c']),
                    'volume': float(candle['v'])
                })
            return candles      
        except client.RemoteDisconnected as e:
            print(f"RemoteDisconnected error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_order_book(self, symbol, limit = 100):
        try:
            if limit > 100:
                limit = 100

            request = self.public_client.depth_v3(
                symbol=symbol,
                limit=limit
            )

            order_book = {
                'bids': [],
                'asks': []
            }

            data = request['data']
            for bid in data.get('b', []):
                order_book['bids'].append({
                    'price': float(bid[0]),
                    'qty': float(bid[1])
                })

            for ask in data.get('a', []):
                order_book['asks'].append({
                    'price': float(ask[0]),
                    'qty': float(ask[1])
                })

            return order_book
        except client.RemoteDisconnected as e:
            print(f"RemoteDisconnected error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        
    def get_coin_by_token_id(self, token_id: str):
        try:
            if token_id in self.coins:
                return self.coins[token_id]
            
            request = self.public_client.configs_v3()
            data = request['data']

            if self.account_type == "S":
                coins = data.get('spotConfig', {}).get('assets', [])
            elif self.account_type == "P":
                coins = data.get('contractConfig', {}).get('assets', [])
            else:
                raise Exception("Invalid account type. Use 'S' for Spot or 'P' for Perpetual.")

            for coin in coins:
                if coin['tokenId'] == token_id:
                    self.coins[token_id] = coin
                    return coin 
            return None
            
        except client.RemoteDisconnected as e:
            print(f"RemoteDisconnected error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_coin_by_name(self, name: str):
        try:
            request = self.public_client.configs_v3()
            data = request['data']

            coins = data.get('contractConfig', {}).get('tokens', [])

            for coin in coins:
                if coin['token'].lower() == name.lower():
                    return coin 
            return None
            
        except client.RemoteDisconnected as e:
            print(f"RemoteDisconnected error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

