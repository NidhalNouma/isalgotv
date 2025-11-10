# PERP Contract are in base Coin in case of not enough balance the size will be adjusted to max available 

from hyperliquid.info import Info
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange

import eth_account
from eth_account.signers.local import LocalAccount

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

import time

class HyperliquidClient(CryptoBrokerClient):
    def _setup(self, base_url=None, skip_ws=False, perp_dexs=None):

        account: LocalAccount = eth_account.Account.from_key(self.api_secret)
        address = self.api_key
        if address == "":
            address = account.address
        print("Running with account address:", address)
        if address != account.address:
            print("Running with agent address:", account.address)
        info = Info(base_url, skip_ws, perp_dexs=perp_dexs)
        exchange = Exchange(account, base_url, account_address=address, perp_dexs=perp_dexs)
        return address, info, exchange

    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        super().__init__(account, api_key, api_secret, passphrase, account_type, current_trade)

        address, info, exchange = self._setup(constants.MAINNET_API_URL, skip_ws=True)

        self.info = info
        self.exchange = exchange
        self.address = address


    @staticmethod
    def check_credentials(api_key, api_secret, account_type='S'):
        try:
            client = HyperliquidClient(api_key=api_key, api_secret=api_secret, account_type=account_type)
            user_state = client.info.user_state(client.address)
            spot_user_state = client.info.spot_user_state(client.address)
            margin_summary = user_state["marginSummary"]
            if float(margin_summary["accountValue"]) == 0 and len(spot_user_state["balances"]) == 0:
                print("Not running the example because the provided account has no equity.")
                url = client.info.base_url.split(".", 1)[1]
                error_string = f"No accountValue:\nIf you think this is a mistake, make sure that {client.address} has a balance on {url}.\nIf address shown is your API wallet address, update the config to specify the address of your account, not the address of the API wallet."
                raise Exception(error_string)

            if 'error' in user_state:
                return {'error': user_state['error'], "valid": False}
            
            return {"valid": True, "message": "Credentials are valid."}
        except Exception as e:
            print("Error in credentials:", str(e))
            return {'error': str(e), "valid": False}
    
    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = None, oc = False):
        try:
            symbol = self.adjust_symbol_name(symbol)

            symbol_info = self.get_exchange_info(symbol)
            if not symbol_info:
                raise Exception(f"Symbol {symbol} not found.")
            
            print("Symbol info:", symbol_info)
            
            order_symbol = symbol
            quote_asset = symbol_info.get('quoteAsset', 'USDC')

            adjusted_quantity = self.adjust_trade_quantity(symbol_info, side, quantity)

            coin = symbol.split("-")[0]
            is_buy = side.lower() == "buy"
            if oc:
                order = self.exchange.market_close(coin, sz=float(adjusted_quantity))
            else:
                order = self.exchange.market_open(coin, is_buy=is_buy, sz=float(adjusted_quantity))

            end_exe = time.perf_counter()
            if not order:
                raise Exception("No response from exchange when opening trade.")

            order_data = order.get('response', {}).get('data', {}).get('statuses', [])[0]

            if order_data.get('error'):
                raise Exception(f"{order_data['error']}")

            order_id = order_data.get('filled', {}).get('oid') if order_data else None

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
                    'symbol': symbol,
                    "side": side.upper(),
                    'qty': order_details.get('volume', adjusted_quantity),
                    'price': order_details.get('price', '0'),
                    'time': order_details.get('time', ''),
                    'fees': order_details.get('fees', ''),
                    'currency':  order_details.get('currency') if order_details.get('currency') not in (None, 'None') else quote_asset,

                    'trade_details': trade_details,
                    "end_exe": end_exe
                }
            else:
                raise Exception("Failed to retrieve order details after opening trade.")
        
        except Exception as e:
            print("Error opening trade:", str(e))
            raise Exception(f"Error opening trade: {str(e)}")
    
    def close_trade(self, symbol: str, side: str, quantity: float):
        t_side = "sell" if side.lower() == "buy" else "buy"
        custom_id = self.current_trade.custom_id if self.current_trade else None
        return self.open_trade(symbol, t_side, quantity, custom_id=custom_id, oc=True)
    
    def get_order_info(self, symbol, order_id):
        try:
            symbol = self.adjust_symbol_name(symbol)
            coin = symbol.split("-")[0]
            orders = self.info.user_fills(self.address)
            if not orders or 'error' in orders:
                raise Exception(f"Error fetching order info: {orders.get('error', 'No data returned')}")

            trades = [o for o in orders if o.get('oid') == order_id]

            if len(trades) == 0:
                raise Exception(f"Order with ID {order_id} not found.")

            total_size = sum(float(trade.get('sz', 0)) for trade in trades)
            
            total_pnl = sum(float(trade.get('closedPnl', 0)) for trade in trades)
            total_fees = sum(float(trade.get('fee', 0)) for trade in trades)

            trade = trades[0]
            # return trades
            r = {
                'order_id': str(trade.get('oid')),
                'symbol': str(trade.get('coin')),
                'volume': str(total_size),
                'side': str(trade.get('side')),
                
                'time': self.convert_timestamp(trade.get('time')),
                'price': str(trade.get('px')),

                'profit': str(total_pnl),
                'fees': str(total_fees),

                'currency': str(trade.get('feeToken')),

                'additional_info': {
                    'hash': str(trade.get('hash')),
                    'dir': str(trade.get('dir')),
                    'startPosition': str(trade.get('startPosition')),
                },
            }

            return r
        except Exception as e:
            print("Error fetching order info:", str(e))
            return None
    
    def adjust_symbol_name(self, symbol):
        symbol = symbol.replace("/", "-")
        if "-" not in symbol:
            if symbol.endswith("USDC"):
                symbol = symbol[:-4] + "-USDC"
            elif symbol.endswith("USDT"):
                symbol = symbol[:-4] + "-USDT"
            elif symbol.endswith("USD"):
                symbol = symbol[:-3] + "-USD"
        return symbol


    def get_exchange_info(self, symbol):
        try:
            symbol = self.adjust_symbol_name(symbol)
            coin, quote = symbol.split("-")
            req = self.info.meta_and_asset_ctxs()
            symbols = req[0].get('universe', [])
            data = [sym for sym in symbols if sym['name'] == coin]
            sym = data[0] if data else None
            if not sym:
                raise Exception(f"Symbol {symbol} not found.")
            return {
                "symbol": sym.get('name'),
                "base_asset": coin,
                "quote_asset": quote,
                "base_decimals": sym.get('szDecimals'),
                "quote_decimals": sym.get('szDecimals'),
            }
        except Exception as e:
            print("Error fetching exchange info:", str(e))
            return None
    
    
    def get_current_price(self, symbol):
        try:
            
            markets = self.info.all_mids()
            return markets

        except Exception as e:
            print("Error fetching ticker:", str(e))
            return None
        
    def get_account_balance(self, symbol=None):
        try:
            if self.account_type == "P":
                account = self.info.user_state(self.address)
                # balances = account["balances"]
                return_balances = {
                    'USDC': {"available": account['marginSummary']['accountValue']}
                }
                return return_balances
            else:
                spot_user_state = self.info.spot_user_state(self.address)
                balances = spot_user_state["balances"]
                print("Fetched balances:", balances)
                balance_dict = {}
                for bal in balances:
                    asset = bal["coin"]
                    if symbol is not None and asset not in symbol:
                        continue
                    free = float(bal["token"])
                    locked = float(bal["hold"])
                    total = free + locked
                    balance_dict[asset] = {
                        "available": free,
                        "locked": locked,
                        "total": total
                    }
                return balance_dict
        except Exception as e:
            print("Error fetching account balance:", str(e))
            return {}
    
    def get_trading_pairs(self):
        try:
            req = self.info.meta_and_asset_ctxs()
            symbols = req[0].get('universe', [])
            data = [sym['name'] for sym in symbols]
            return [f"{sym}-USDC" for sym in data]
        except Exception as e:
            print("Error fetching trading pairs:", str(e))
            return []
    
    def get_history_candles(self, symbol, interval, limit = 500):
        try:
            symbol = self.adjust_symbol_name(symbol)
            coin = symbol.split("-")[0]
            interval_map = {
                "1m": 60,
                "3m": 180,
                "5m": 300,
                "15m": 900,
                "30m": 1800,
                "1h": 3600,
                "2h": 7200,
                "3h": 10800,
                "4h": 14400,
                "8h": 28800,
                "12h": 43200,
                "1d": 86400,
                "1w": 604800,
                "1M": 2592000
            }
            if interval not in interval_map:
                raise Exception(f"Unsupported interval: {interval}")
            interval_seconds = interval_map[interval]
            start_time = int(time.time() * 1000) - (limit * interval_seconds * 1000)
            end_time = int(time.time() * 1000)

            candles = self.info.candles_snapshot(coin, interval, start_time, end_time)
            formatted_candles = []
            for candle in candles:
                formatted_candles.append({
                    "time": self.convert_timestamp(candle['t']),
                    "open": candle['o'],
                    "high": candle['h'],
                    "low": candle['l'],
                    "close": candle['c'],
                    "volume": candle['v']
                })
            return formatted_candles
        except Exception as e:
            print("Error fetching historical candles:", str(e))
            return []
    
    def get_order_book(self, symbol, limit = 100):
        pass