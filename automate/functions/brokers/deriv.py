# Only Options trading accounts are supported through this API
# Multiplier contracts only
# Partial closures not supported
# Forex, Commodities, Indices and Crypto supported via MULTUP and MULTDOWN contracts
# Multiplier is set to 500 by default for better profit potential

import asyncio
import websockets
import json
import threading
import time
from django.utils import timezone

from automate.functions.brokers.broker import BrokerClient
from automate.functions.brokers.types import *

import environ
env = environ.Env()

APP_ID = env('DERIV_APP_ID')
DERIV_WS = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"


class DerivClient(BrokerClient):
    def __init__(self, account=None, username=None, password=None, server=None, type='L', account_id=None, current_trade=None):
        self.token = None
        self.symbols_cache = {}
        self.current_trade = current_trade
        
        if account:
            self.token = account.server
            self.account_id = account.account_api_id
            self.account = account  
        else:
            self.token = server
            self.account_id = account_id
            self.account = None

        self.ws = None
        self.loop = None
        self.loop_thread = None
        self._start_event_loop()
        self._connect_ws()

        authorize = self._send_request({
            "authorize": self.token
        })
        if "error" in authorize:
            if 'message' in authorize["error"]:
                raise Exception(authorize["error"]["message"])
            raise Exception(authorize["error"])
        print("Deriv websocket connected and authorized once.")

    # --------------------------------------------------------------
    # Create dedicated event loop in a background thread
    # --------------------------------------------------------------
    def _start_event_loop(self):
        self.loop = asyncio.new_event_loop()

        def loop_runner(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self.loop_thread = threading.Thread(target=loop_runner, args=(self.loop,), daemon=True)
        self.loop_thread.start()

    # --------------------------------------------------------------
    # Connect websocket once
    # --------------------------------------------------------------
    async def _async_connect_ws(self):
        self.ws = await websockets.connect(DERIV_WS)

    def _connect_ws(self):
        future = asyncio.run_coroutine_threadsafe(self._async_connect_ws(), self.loop)
        future.result()

    # --------------------------------------------------------------
    # Send request on persistent websocket
    # --------------------------------------------------------------
    async def _async_send(self, data):
        if self.ws is None:
            raise Exception("Websocket is not connected.")
        await self.ws.send(json.dumps(data))
        response_raw = await self.ws.recv()
        response = json.loads(response_raw)
        return response

    def _send_request(self, data):
        future = asyncio.run_coroutine_threadsafe(self._async_send(data), self.loop)
        response = future.result()
        if "error" in response:
            msg = response["error"].get("message", response["error"])
            raise Exception(msg)
        return response
        
    @staticmethod
    def check_credentials(token: str, account_id: str, type: str = 'D'):
        try:
            print("Checking Deriv credentials...", account_id)
            if not token or not account_id:
                raise Exception("Token and Account ID must be provided.")
            client = DerivClient(server=token, account_id=account_id, type=type)
            account_info = client.get_account_info()
            # print("Account Info:", account_info)
            if account_info.get('account_category') not in ['trading']:
                raise Exception("Account is not a trading account.")
            
            account_type = 'L' if account_info.get('is_virtual', 0) == 1 else 'D'

            return {
                "valid": True,  
                "message": "Deriv credentials are valid.",
                "account_api_id": account_id,
                "account_type": account_type,
                "additional_info": {
                    'account_info': account_info,
                    'multiplier': 500
                }
            }
        except Exception as e:
            return {
                "error": str(e),
                "message": "Invalid Deriv credentials.",
                "valid": False
            }
        
    def get_account_info(self):
        try:
            account_info = self._send_request({
                "account_list": 1,
            })
            accounts = account_info.get("account_list", [])
            for account in accounts:
                if str(account.get("loginid")) == str(self.account_id):
                    return account
            raise Exception("Account ID not found.")
        except Exception as e:
            print("Error getting account info:", str(e))
            raise e
    
    def get_account_balance(self, symbol = None):
        try:
            balance_info = self._send_request({
                "balance": 1,
            })
            return balance_info.get("balance")
        except Exception as e:
            print("Error getting account balance:", str(e))
            raise e
    
    def open_trade(self, symbol, side, quantity, custom_id=''):
        try:
            decimals = 2
            adjusted_quantity = round(float(quantity), decimals)
            proposal = self.get_proposal(symbol, side, adjusted_quantity)
            if not proposal:
                raise Exception("Failed to get proposal for the trade.")
            
            print(f"Opening trade for {symbol}: side={side}, qty={adjusted_quantity}")

            request = {
                "buy": proposal.get("id"),
                "price": adjusted_quantity,
            }
            req = self._send_request(request)
            order_id = req.get("buy", {}).get("contract_id", None)

            end_exe = time.perf_counter()

            if not order_id:
                raise Exception("Failed to open trade, no contract ID returned.")

            order_info = self.get_order_info(symbol, order_id)
            # print(f"Trade opened successfully for {symbol} with order ID {order_id}: {order_info}")
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'end_exe': end_exe,
                'order_id': order_id,
                'symbol': symbol,
                'side': side,
                'qty': adjusted_quantity,
                'price': order_info.get("price"),
                'time': order_info.get("time"),
                'fees': order_info.get("fees", 0),
                'currency': order_info.get("currency", self.account_currency),
            }
        
        except Exception as e:
            print("Error opening trade:", str(e))
            raise e

    def close_trade(self, symbol, side, quantity):
        try:
            if not self.current_trade:
                raise Exception("No current trade to close.")
            order_id = self.current_trade.order_id
            if not order_id:
                raise Exception("Current trade does not have an order ID.")
            request = {
                "sell": order_id,
                "price": 0,
            }
            req = self._send_request(request)
            end_exe = time.perf_counter()

            trade_details = self.get_final_trade_details(self.current_trade)
            return {
                'message': f"Trade closed with order ID {order_id}.",
                'order_id': order_id,
                'symbol': symbol,
                'qty': self.current_trade.volume,
                'end_exe': end_exe,
                'trade_details': trade_details
            }
        except Exception as e:
            print("Error closing trade:", str(e))
            raise e

    def get_order_info(self, symbol, order_id):
        try:
            trade_info = self._send_request({
                "proposal_open_contract": 1,
                "contract_id": order_id
            })
            cntr = trade_info.get("proposal_open_contract", {})
            # print(cntr)
            
            if not cntr:
                raise Exception(f"No information found for order ID {order_id}.")
            
            return {
                'order_id': order_id,
                'symbol': cntr.get("underlying", ""),
                'qty': cntr.get('buy_price'),
                'price': cntr.get('current_spot'),
                'time': str(self.convert_timestamp(cntr.get('current_spot_time') * 1000) if cntr.get('current_spot_time') else None),
                'fees': cntr.get('commission'),
                'currency': cntr.get('currency'),
            }
        except Exception as e:
            print("Error getting order info:", str(e))
            raise e
        
    
    def get_final_trade_details(self, trade):
        try:
            order_id = trade.order_id
            if not order_id:
                raise Exception("Trade does not have an order ID.")
            trade_info = self._send_request({
                "proposal_open_contract": 1,
                "contract_id": order_id
            })
            cntr = trade_info.get("proposal_open_contract", {})
            if not cntr:
                raise Exception(f"No information found for order ID {order_id}.")
            return {
                'order_id': order_id,
                'symbol': trade.symbol,
                'open_price': cntr.get('entry_spot'),
                'close_price': cntr.get('sell_spot'),
                'open_time': str(self.convert_timestamp(cntr.get('entry_tick_time') * 1000) if cntr.get('entry_tick_time') else timezone.now()),
                'close_time': str(self.convert_timestamp(cntr.get('sell_spot_time') * 1000) if cntr.get('sell_spot_time') else timezone.now()),
                'profit': cntr.get('profit'),
            }
        except Exception as e:
            print("Error getting final trade details:", str(e))
            raise e

    def get_open_trades(self):
        try:
            open_trades = self._send_request({
                "portfolio": 1,
            })
            portfolio = open_trades.get("portfolio", {})
            return portfolio.get("contracts", [])
        except Exception as e:
            print("Error getting open trades:", str(e))
            raise e

    def get_closed_trades(self, limit=100):
        try:
            closed_trades = self._send_request({
                "profit_table": 1,
                "description": 1,
                "limit": limit,
                "sort": "ASC"
            })
            profit_table = closed_trades.get("profit_table", {})
            return profit_table.get("transactions", [])
        except Exception as e:
            print("Error getting closed trades:", str(e))
            raise e

    @property
    def account_currency(self):
        try:
            if self.account:
                curr = self.account.additional_info.get('account_info', {}).get('currency', None)
                if curr:
                    return curr
                
            account_info = self.get_account_info()
            currency = account_info.get("currency")
            if not currency:
                raise Exception("Currency information not found in account info.")
            return currency
        except Exception as e:
            print("Error getting account currency:", str(e))
            raise e

    def get_trading_pairs(self):
        try:
            pairs = self._send_request(
                {
                    'active_symbols': 'brief',
                    'product_type': 'basic'
                }
            )
            return pairs.get("active_symbols", [])
        except Exception as e:
            print("Error getting trading pairs:", str(e))
            raise e

    def get_symbol_info(self, symbol: str):
        try:
            if symbol in self.symbols_cache:
                return self.symbols_cache[symbol]
            pairs = self.get_trading_pairs()
            for item in pairs:
                if str(item.get("display_name")).upper() == symbol.upper() or str(item.get("display_name", "")).replace("/", "").upper() == symbol.upper() or str(item.get("symbol")).upper() == symbol.upper():
                    self.symbols_cache[symbol] = item
                    return item
            raise Exception(f"Symbol {symbol} not found.")
        except Exception as e:
            print("Error getting symbol info:", str(e))
            raise e
        
    def get_proposal(self, symbol, side, quantity):
        try:
            symbol_info = self.get_symbol_info(symbol)
            multiplier = 500 if self.account and self.account.additional_info.get('multiplier') is None else self.account.additional_info.get('multiplier', 500)
            proposal = self._send_request({
                "proposal": 1,
                "amount": quantity,
                "basis": "stake",
                "contract_type": "MULTUP" if side.lower() == "buy" else "MULTDOWN",
                "multiplier": multiplier,
                "currency": self.account_currency,
                "symbol": symbol_info.get("symbol")
            })
            return proposal.get("proposal", {})
        except Exception as e:
            print("Error getting proposal:", str(e))
            raise e

    def get_current_price(self, symbol):
        try:
            symbol_info = self.get_symbol_info(symbol)
            proposal = self._send_request({
                "proposal": 1,
                "amount": 1,
                "basis": "stake",
                "contract_type": "MULTUP",
                "multiplier": 50,
                "currency": self.account_currency,
                "symbol": symbol_info.get("symbol")
            })
            proposal = proposal.get("proposal", {})
            return proposal.get("spot")
        except Exception as e:
            raise e

    def get_history_candles(self, symbol, timeframe, limit=100):
        pass

    def market_and_account_data(self, symbol: str, intervals: List[str], limit: int = 500) -> dict:
        try:
            history_candles = {}
            for interval in intervals:
                try:
                    candles = self.get_history_candles(symbol, interval, limit)
                    history_candles[interval] = candles
                except Exception as e:
                    print(f"Error getting history candles for interval {interval}:", str(e))

            try:
                account_info = self.get_account_info()
            except Exception as e:
                print("Error getting account info:", str(e))
                account_info = {}

            try:
                balance = self.get_account_balance()
            except Exception as e:
                print("Error getting account balance:", str(e))
                balance = None

            try:
                symbol_info = self.get_symbol_info(symbol)
            except Exception as e:
                print("Error getting symbol info:", str(e))
                symbol_info = {}

            try:
                current_price = self.get_current_price(symbol)
            except Exception as e:
                print("Error getting current price:", str(e))
                current_price = None

            return {
                "history_candles": history_candles,
                "account_info": account_info,
                "balance": balance,
                "symbol_info": symbol_info,
                "current_price": current_price
            }
        except Exception as e:
            print("Error getting market and account data:", str(e))
            raise e

    async def _async_close(self):
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self.loop.is_running():
            self.loop.stop()

    def close(self):
        try:
            asyncio.run_coroutine_threadsafe(self._async_close(), self.loop)
            if self.loop_thread:
                self.loop_thread.join(timeout=1)
            print("Deriv websocket connection closed.")
        except:
            pass

    def __del__(self):
        self.close()