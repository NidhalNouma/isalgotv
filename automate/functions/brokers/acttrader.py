import requests
import time
from dateutil import parser
from django.utils import timezone
from uuid import uuid4


from automate.functions.brokers.broker import BrokerClient
from automate.functions.brokers.types import *


class ActTrader(BrokerClient):
    def __init__(self, account=None, username=None, password=None, server=None, type=None, current_trade=None):
        super().__init__()

        self.API_URL = ""
        self.account_id = None

        if account:
            self.username = account.username
            self.password = account.password
            self.type = account.type
        else:
            self.username = username
            self.password = password
            self.type = type

        self.accessToken = None

        self.s = requests.Session()
        self.current_trade = current_trade

    @staticmethod
    def check_credentials(username, password, type):
        """
        Tries to log in with the given credentials. Returns {"error": str, "valid": False} on failure.
        """
        try:
            client = ActTrader(username=username, password=password, type=type)
            client.login()
            if client.accessToken is None or client.account_id is None:
                raise Exception("Login failed")
            return {"error": None, "valid": True}
        except Exception as e:
            return {"error": str(e), "valid": False}

    def login(self):
        url = f"{self.API_URL}/api/v2/auth/token"
        params = {
            "lifetime": 20 # Token lifetime in minutes
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Basic Auth credentials
        auth = (self.username,  self.password)

        response = self.s.get(url, params=params, headers=headers, auth=auth)
        response = response.json()

        if response.get('success', False):
            self.accessToken = response.get('result', '')

            account = self.get_account_info()
            self.account_id = account.get('AccountID', None)
        else:
            raise Exception("Login failed: " + response.get('message', 'Unknown error'))
        
    def get_account_info(self):
        try:
            url = f"{self.API_URL}/api/v2/account/accounts"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.accessToken}"
            }

            params = {
                "token": self.accessToken
            }

            response = self.s.get(url, params=params, headers=headers)
            response = response.json()

            if response.get('success', False):
                accounts = response.get('result', [])
                # print('Accounts found:', accounts)
                if accounts:
                    return accounts[0]  # Return the first account
                else:
                    raise Exception("No accounts found.")
            else:
                raise Exception("Failed to get account info: " + response.get('message', 'Unknown error'))
        except Exception as e:
            raise Exception("Get account info Error: %s" % e)

    def get_account_currency(self):
        try:
            account_info = self.get_account_info()
            currency = account_info.get('Currency', 'USD')
            return currency
        except Exception as e:
            raise Exception("Get currency Error: %s" % e)

    def get_account_balance(self, symbol: str = None):
        try:
            account_info = self.get_account_info()
            balance = account_info.get('Balance', 0.0)
            equity = account_info.get('Equity', 0.0)
            return balance, equity
        except Exception as e:
            raise Exception("Get balance Error: %s" % e)
        
    def adjust_symbol_name(self, symbol: str) -> str:
        return symbol
        
    def get_symbol_info(self, symbol):
        try:
            symbol = self.adjust_symbol_name(symbol)
            url = f"{self.API_URL}/api/v2/market/symbols"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            params = {
                "token": self.accessToken,
                "symbol": symbol
            }

            response = self.s.get(url, params=params, headers=headers)
            response = response.json()

            if response.get('success', False):
                instruments = response.get('result', [])
                for inst in instruments:
                    if inst['Symbol'] == symbol:
                        return inst
                raise Exception(f"Symbol {symbol} not found.")
            else:
                raise Exception("Failed to get symbol info: " + response.get('message', 'Unknown error'))
        except Exception as e:
            raise Exception("Get symbol Error: %s" % e) 

    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = "") -> OpenTrade:
        try:
            symbol = self.adjust_symbol_name(symbol)

            symbol_info = self.get_symbol_info(symbol)
            contract_size = symbol_info.get('ContractSize', 1)
            quantity = float(quantity) * float(contract_size)

            url = f"{self.API_URL}/api/v2/trading/placemarket"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            order_type = 1 if str.upper(side) in ("BUY", "B") else 0

            custom_id = custom_id + f"_{str(uuid4())}"

            params = {
                "token": self.accessToken,
                "account": self.account_id,
                "symbol": symbol,
                "side": order_type,
                "quantity": quantity,
                "commentary": custom_id
            }

            response = self.s.get(url, params=params, headers=headers)

            end_exe = time.perf_counter()
            response = response.json()

            if response.get('success', False):
                trade_info = response.get('result', {})
                order_id = trade_info.get('OrderID', None)
                orderInfo = self.get_open_trade_by_custom_id(symbol, custom_id)
                # print(orderInfo)
                return {
                    'message': f"Trade opened with order ID {order_id}.",
                    'order_id': orderInfo.get('trade_id'),
                    'symbol': symbol,
                    'price': orderInfo.get('price'),
                    'time': orderInfo.get('time'),
                    'qty': quantity,
                    'currency': self.get_account_currency(),
                    'end_exe': end_exe,
                }
            else:
                raise Exception("Failed to open trade: " + response.get('message', 'Unknown error'))
        except Exception as e:
            raise Exception("Open trade Error: %s" % e)
            


    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        try:
            symbol = self.adjust_symbol_name(symbol)

            # symbol_info = self.get_symbol_info(symbol)
            # contract_size = symbol_info.get('ContractSize', 1)
            
            quantity = float(quantity) 

            url = f"{self.API_URL}/api/v2/trading/closetrade"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            order_type = 0 if str.upper(side) in ("BUY", "B") else 1

            params = {
                "token": self.accessToken,
                "trade": self.current_trade.order_id,
                "symbol": symbol,
                "side": order_type,
                "quantity": quantity
            }

            response = self.s.get(url, params=params, headers=headers)

            end_exe = time.perf_counter()
            response = response.json()
            # print('Close trade response:', response)

            if response.get('success', False):
                trade_info = response.get('result', {})
                order_id =  self.current_trade.order_id
                
                closed_position = self.get_closed_trades(symbol, order_id)

                return {
                    'message': f"Trade closed with order ID {order_id}.",
                    'order_id': order_id,
                    'symbol': symbol,
                    'qty': quantity,
                    'closed_order_id': order_id,
                    'trade_details': closed_position,
                    'end_exe': end_exe,
                }

            else:
                raise Exception(response.get('message', 'Unknown error'))
        except Exception as e:
            raise Exception("Close trade Error: %s" % e)
        
    def get_order_info(self, symbol, order_id):
        symbol = self.adjust_symbol_name(symbol)
        order = self.get_open_trade(symbol, order_id)
        if order is None:
            order = self.get_closed_trades(symbol, order_id)
        return order
    
    def get_open_trade_by_custom_id(self, symbol, custom_id: str) -> OrderInfo:
        try:
            symbol = self.adjust_symbol_name(symbol)

            url = f"{self.API_URL}/api/v2/trading/opentrades"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            params = {
                "token": self.accessToken
            }

            response = self.s.get(url, params=params, headers=headers)
            response = response.json()

            if response.get('success', False):
                open_trades = response.get('result', [])
                trade = next((t for t in open_trades if t.get('Commentary') == custom_id), None)
                # print('Trade found by custom_id:', trade)
                if trade is None:
                    return None
                time_str = trade.get("OpenTime")
                if time_str:
                    parsed_time = parser.isoparse(time_str)
                    if timezone.is_naive(parsed_time):
                        parsed_time = timezone.make_aware(parsed_time)
                else:
                    parsed_time = None
                return {
                    "trade_id": trade.get("TradeID"),
                    "symbol": trade.get("Symbol"),
                    "side": "BUY" if trade.get("Side") == 1 else "SELL",
                    "qty": trade.get("Quantity"),
                    "price": trade.get("Price"),
                    "time": parsed_time.isoformat() if parsed_time else None,
                    "fees": (trade.get("Commission") or 0) + (trade.get("Interest") or 0),
                    "currency": self.get_account_currency()
                }
            else:
                raise Exception("Failed to get open trades: " + response.get('message', 'Unknown error'))
        except Exception as e:
            raise Exception("Get trade error: %s" % e)

    def get_open_trade(self, symbol, trade_id: str) -> OrderInfo:
        try:
            symbol = self.adjust_symbol_name(symbol)
            url = f"{self.API_URL}/api/v2/trading/opentrades"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            params = {
                "token": self.accessToken
            }

            response = self.s.get(url, params=params, headers=headers)
            response = response.json()

            if response.get('success', False):
                open_trades = response.get('result', [])
                trade = next((t for t in open_trades if str(t.get('TradeID')) == str(trade_id)), None)
                if trade is None:
                    raise Exception(f"Open trade with ID {trade_id} not found.")
                
                time_str = trade.get("OpenTime")
                if time_str:
                    parsed_time = parser.isoparse(time_str)
                    if timezone.is_naive(parsed_time):
                        parsed_time = timezone.make_aware(parsed_time)
                else:
                    parsed_time = None
                return {
                    "trade_id": trade.get("TradeID"),
                    "symbol": trade.get("Symbol"),
                    "side": "BUY" if trade.get("Side") == 1 else "SELL",
                    "qty": trade.get("Quantity"),
                    "price": trade.get("Price"),
                    "time": parsed_time.isoformat() if parsed_time else None,
                    "fees": trade.get("Commission") + trade.get("Interest"),
                    "currency": self.get_account_currency()
                }
            else:
                raise Exception("Failed to get open trades: " + response.get('message', 'Unknown error'))
        except Exception as e:
            raise Exception("Get open trade error: %s" % e)
        
    def get_closed_trades(self, symbol: str, trade_id: str, from_date: str = None, to_date: str = None) -> list:
        try:
            symbol = self.adjust_symbol_name(symbol)
            url = f"{self.API_URL}/api/v2/trading/tradehistory"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            params = {
                "token": self.accessToken,
                "account": self.account_id,
                "tradeID": trade_id
            }

            if from_date:
                params['from'] = from_date
            if to_date:
                params['to'] = to_date

            response = self.s.get(url, params=params, headers=headers)
            response = response.json()

            if response.get('success', False):
                closed_trades = response.get('result', [])

                response_trades = []
                for trade in closed_trades:

                    open_time_str = trade.get("OpenTime")
                    if open_time_str:
                        parsed_open_time = parser.isoparse(open_time_str)
                        if timezone.is_naive(parsed_open_time):
                            parsed_open_time = timezone.make_aware(parsed_open_time)
                    else:
                        parsed_open_time = None
                    close_time_str = trade.get("CloseTime")
                    if close_time_str:
                        parsed_close_time = parser.isoparse(close_time_str)
                        if timezone.is_naive(parsed_close_time):
                            parsed_close_time = timezone.make_aware(parsed_close_time)
                    else:
                        parsed_close_time = None
                    response_trades.append({
                        "trade_id": trade.get("TradeID"),
                        "symbol": trade.get("Symbol"),
                        "side": "BUY" if trade.get("Side") == 1 else "SELL",
                        "volume": trade.get("Quantity"),
                        "open_price": trade.get("OpenPrice"),
                        "close_price": trade.get("ClosePrice"),
                        "open_time": parsed_open_time.isoformat() if parsed_open_time else None,
                        "close_time": parsed_close_time.isoformat() if parsed_close_time else None,
                        "fees": trade.get("Commission") + trade.get("Interest"),
                        "profit": trade.get("ProfitLoss"),
                    })
                
                response_trades.sort(key=lambda t: t["close_time"] or "")
                return response_trades
            else:
                raise Exception("Failed to get closed trades: " + response.get('message', 'Unknown error'))
        except Exception as e:
            raise Exception("Get closed trades Error: %s" % e)

    def get_current_price(self, symbol):
        try:
            symbol = self.adjust_symbol_name(symbol)
            symbol_info = self.get_symbol_info(symbol)
            bid = symbol_info.get('Buy', None)
            ask = symbol_info.get('Sell', None)
            if bid is None or ask is None:
                raise Exception(f"Could not retrieve current price for symbol {symbol}")
            return {
                "bid": bid,
                "ask": ask
            }
        except Exception as e:
            raise Exception("Get price Error: %s" % e)

    def get_trading_pairs(self):
        try:
            url = f"{self.API_URL}/api/v2/market/symbols"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            params = {
                "token": self.accessToken
            }

            response = self.s.get(url, params=params, headers=headers)
            response = response.json()

            if response.get('success', False):
                instruments = response.get('result', [])
                symbols = [inst['Symbol'] for inst in instruments]
                return symbols
            else:
                raise Exception("Failed to get trading pairs: " + response.get('message', 'Unknown error'))
        except Exception as e:
            raise Exception("Get trading pairs Error: %s" % e)

    def get_history_candles(self, symbol, interval, limit = 500):
        symbol = self.adjust_symbol_name(symbol)
        pass

    def market_and_account_data(self, symbol: str, intervals: list, limit: int = 500) -> dict:

        try:
            symbol = self.adjust_symbol_name(symbol)
            balance, equity = self.get_account_balance(symbol)
            symbol_info = self.get_symbol_info(symbol)

            data = {
                "symbol_info": symbol_info,
                "balance": balance,
                "equity": equity,
            }

            return data
        except Exception as e:
            raise Exception("Market and account data Error: %s" % e)

         

class HankoTradeClient(ActTrader):
    def __init__(self, account=None, username=None, password=None, server=None, type=None, current_trade=None):
        super().__init__(account, username, password, server, type, current_trade)

        if self.type == 'L':
            self.API_URL = f"http://s257.hankotrade.com:10101"
        else:
            self.API_URL = f"http://s257demo.hankotrade.com:10101"

        self.login()

    @staticmethod
    def check_credentials(username, password, type):
        """
        Tries to log in with the given credentials. Returns {"error": str, "valid": False} on failure.
        """
        try:
            client = HankoTradeClient(username=username, password=password, type=type)
            if client.accessToken is None:
                raise Exception("Login failed")
            return {"error": None, "valid": True}
        except Exception as e:
            return {"error": str(e), "valid": False}
        
    def adjust_symbol_name(self, symbol: str) -> str:
        if not symbol.endswith('.HKT'):
            symbol = symbol + '.HKT'
        return symbol