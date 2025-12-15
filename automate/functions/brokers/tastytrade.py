import time
import requests
from django.utils.dateparse import parse_datetime

from automate.functions.brokers.broker import BrokerClient
from automate.functions.brokers.types import *


class TastytradeClient(BrokerClient):
    def __init__(self, account=None, username=None, password=None, server=None, type='L', account_id=None, current_trade=None):
        self.s = requests.Session()
        self.accessToken = None
        self.symbols_cache = {}
        self.current_trade = current_trade

        self.account_currency = self.current_trade.currency if self.current_trade else None

        if account:
            self.username = account.username
            self.password = account.password
            self.account_number = account.account_api_id if account.account_api_id else None
            self.type = account.type
        else:
            self.username = username
            self.password = password
            self.account_number = account_id
            self.type = type

        self.API_URL = "https://api.tastytrade.com"
        if self.type.lower() in ['d', 'demo']:
            self.API_URL = "https://api.cert.tastyworks.com"

            self._login_with_password()
        else:
            self._login()

    @staticmethod
    def check_credentials(username: str, password: str, server: str, type: str, account_id: str = None):
        try:
            client = TastytradeClient(
                username=username,
                password=password,
                server=server,
                type=type,
                account_id=account_id
            )

            if not client.accessToken:
                msg = "Invalid credentials. If you received an email to allow access, please follow the instructions in the email and try again."
                return {'error': msg, 'valid': False}
            print("Access token obtained successfully.")

            if not client.account_number:
                first_customer = client.get_first_customer()
                
                if first_customer and first_customer.get("account-number"):
                    client.account_number = first_customer.get("account-number")
                else:
                    return {'error': "Account ID not provided and could not be retrieved.", 'valid': False}
            
            account_info = client.get_account_info()

            if account_info:
                additional_info = {}
                    
                return {'valid': True, 'message': "Credentials are valid.", 'additional_info': additional_info, 'account_api_id': client.account_number}
            else:
                return {'error': "Invalid credentials.", 'valid': False}

        except Exception as e:
            return {'error': str(e), 'valid': False}
        
    def _send_request(self, method, endpoint, params=None, data=None, headers=None, auth=None, timeout=10, with_auth_header=True, max_retries=4):
        url = f"{self.API_URL}{endpoint}"
        if headers is None:
            headers = {}

        if with_auth_header and self.accessToken:
            headers["Authorization"] = f"{self.accessToken}"
        
        response = self.retry_until_response(
            func=self.s.request,
            is_desired_response=lambda r: r.status_code >= 200 and r.status_code < 300,
            args=(method, url),
            kwargs={
                "params": params,
                "json": data,
                "headers": headers,
                "auth": auth,
                "timeout": timeout
            },
            max_attempts=max_retries,
            delay_seconds=2
        )
        if response.status_code < 200 or response.status_code >= 300:
            error = response.json().get("error", response.text)
            if type(error) == dict:
                if error.get('errors'):
                    message_errors = [e.get('message', str(e)) for e in error.get('errors')]
                    error = "\n".join(message_errors)
                else:
                    error = error.get('message', str(error))
            raise Exception(f"HTTP Error {response.status_code}: {error}")
        return response.json()
    
    def _login(self):
        try:
            login_data = {
                "grant_type": "refresh_token",
                "refresh_token": self.username,
                "client_secret": self.password
            }

            response = self._send_request("POST", "/oauth/token", data=login_data, with_auth_header=False, max_retries=1)

            if response.get("error"):
                raise Exception(f"Login failed: {response.get('error')}")
            accessToken = response.get("access_token")
            if not accessToken:
                raise Exception("Login failed: Access token not found.")
            self.accessToken = f"Bearer {accessToken}"
        except Exception as e:
            print(f"Login error: {e}")
            raise e
    
    def _login_with_password(self):
        try:
            login_data = {
                "login": self.username,
                "password": self.password,
                "remember-me": True
            }

            response = self._send_request("POST", "/sessions", data=login_data, with_auth_header=False, max_retries=1)
            data = response.get("data", {})
            if data.get("error"):
                raise Exception(f"Login failed: {data.get('error')}")
            self.accessToken = data.get("session-token")
            if not self.accessToken:
                raise Exception("Login failed: Access token not found.")
        except Exception as e:
            print(f"Login error: {e}")
            raise e
        
    def get_account_info(self):
        try:
            response = self._send_request("GET", f"/accounts/{self.account_number}/balances")
            if response.get("error"):
                print(f"Error fetching account info: {response.get('error')}")
                return None
            return response.get("data", {})
        except Exception as e:
            print(f"Error fetching account info: {e}")
            return None
        
    def get_first_customer(self):
        try:
            response = self._send_request("GET", "/customers/me/accounts")
            if response.get("error"):
                raise Exception(response.get('error'))
            
            items = response.get("data", {}).get("items", [])
            if items and len(items) > 0:
                return items[0].get("account", None)
            else:
                return None
        except Exception as e:
            print(f"Error fetching customers: {e}")
            return None

    def get_account_balance(self, symbol = None):
        try:
            account = self.get_account_info()
            if not account:
                raise Exception("Account info not found")
            cash_balance = account.get("cash-balance", 0.0)
            currency = account.get("currency", "USD")
            net_liquidating_value = account.get("net-liquidating-value", 0.0)
            return {
                "cash_balance": cash_balance,
                "net_liquidating_value": net_liquidating_value,
                "currency": currency,
            }
        except Exception as e:
            print(f"Error fetching account balance: {e}")
            return None

    def get_symbol_info(self, symbol: str):
        if symbol in self.symbols_cache:
            return self.symbols_cache[symbol]

        try:
            response = self._send_request("GET", f"/symbols/search/{symbol}")
            if response.get("error"):
                print(f"Error fetching symbol info for {symbol}: {response.get('error')}")
                return None
            data = response.get("data", {})
            if data.get('error'):
                print(f"Error fetching symbol info for {symbol}: {data.get('error')}")
                raise Exception(data.get('error'))
            # print(f"Symbol search response data for {symbol}: {data}")
            if data.get("items"):
                symbol_info = data["items"][0]  # Assuming the first item is the desired symbol
                self.symbols_cache[symbol] = symbol_info
                return symbol_info
            else:
                raise Exception("No symbol info found")
        except Exception as e:
            print(f"Error fetching symbol info for {symbol}: {e}")
            return None
        
    def get_current_price(self, symbol):
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return None
            quote_response = self._send_request("GET", f"/quotes/{symbol_info['symbolId']}")
            if quote_response.get("error"):
                raise Exception(quote_response.get('error'))
            quote_data = quote_response.get("data", {})
            return quote_data.get("lastPrice")
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {e}")
            return None
        
    def open_trade(self, symbol: str, side: str, quantity, custom_id = '', oc = False):
        try:
            action = "Buy to Open" if side.lower() == "buy" else "Sell to Open"
            if oc:
                action = "Buy to Close" if side.lower() == "buy" else "Sell to Close"

            sym_info = self.get_symbol_info(symbol)
            print(sym_info)
            if not sym_info:
                raise Exception(f"Symbol info not found for {symbol}")
            
            symbol_name = sym_info.get("symbol")
            symbol_type = sym_info.get("instrument-type")
                
            data = {
                "order-type": "Market",
                "time-in-force": "Day",
                "legs": [
                    {
                        "instrument-type": "Equity" if not symbol_type else symbol_type,
                        "action": action,
                        "quantity": quantity,
                        "symbol": symbol_name
                    }
                ]
            }

            response = self._send_request("POST", f"/accounts/{self.account_number}/orders", data=data, max_retries=1)
            end_exe = time.perf_counter()
            if response.get("error"):
                raise Exception(response.get('error'))
            data = response.get("data", {})
            order_data = data.get("order", {})

            if not order_data:
                raise Exception("Order data not found in response")
            
            order_id = order_data.get("id", None)
            if not order_id:
                raise Exception("Order ID not found in order data")

            order_info = self.get_order_info(symbol, order_id)
            if not order_info:
                raise Exception("Failed to retrieve order info after placing order")
            
            # print(f"Trade opened successfully for {symbol}: {order_info}")
            return order_info
        except Exception as e:
            print(f"Error opening trade for {symbol}: {e}")
            raise e

    def close_trade(self, symbol, side, quantity):
        t_side = "sell" if side.lower() == "buy" else "buy"
        return self.open_trade(symbol, t_side, quantity, oc=True)


    def get_order_by_id(self, symbol, order_id):
        try:
            response = self._send_request("GET", f"/accounts/{self.account_number}/orders/{order_id}")
            if response.get("error"):
                raise Exception(response.get('error'))
            data = response.get("data", {})
            return data
        except Exception as e:
            print(f"Error fetching order info for {symbol}, order ID {order_id}: {e}")
            raise e
        
    def get_order_info(self, symbol, order_id, max_wait=10):
        for i in range(max_wait):
            try:
                resp = self._send_request(
                    "GET",
                    f"/accounts/{self.account_number}/transactions",
                    params={"type": "Trade", "symbol": symbol},
                    max_retries=1
                )
                # print(f"Fill poll response: {resp}")

                items = resp.get("data", {}).get("items", [])
                for t in items:
                    if t.get("order-id") == order_id:
                        order_type = str(t.get("transaction-sub-type", "")).lower()
                        if order_type == "buy to open":
                            order_type = "BUY"
                        elif order_type == "sell to open":
                            order_type = "SELL"

                        price =  t.get("price", 0.0)
                        qty = t.get("quantity", 0.0)
                        profit = 0.0
                        if self.current_trade:
                            open_price = self.current_trade.entry_price
                            if order_type == "SELL":
                                profit = (price - open_price) * qty
                            else:
                                profit = (open_price - price) * qty

                        return {
                            'symbol': t.get("symbol"),
                            "type": order_type,
                            "quantity": qty,
                            "price": price,
                            "time": str(parse_datetime(t.get("executed-at"))),

                            "fees": float(t.get("regulatory-fees", 0)) + float(t.get("commission", 0)) + float(t.get("clearing-fees", 0)),
                            "profit": profit,
                            "currency": t.get("currency"),
                            "additional_info": t
                        }

            except Exception as e:
                print(f"Fill poll error: {e}")

            time.sleep(1)

        return None

    def get_positions(self):
        try:
            response = self._send_request("GET", f"/accounts/{self.account_number}/positions")
            if response.get("error"):
                raise Exception(response.get('error'))
            data = response.get("data", {})
            positions = data.get("items", [])
            return positions
        except Exception as e:
            print(f"Error fetching positions: {e}")
            raise e

    def get_trading_pairs(self):
        try:
            response = self._send_request("GET", "/symbols/trading-pairs")
            if response.get("error"):
                raise Exception(response.get('error'))
            data = response.get("data", {})
            pairs = data.get("items", [])
            return pairs
        except Exception as e:
            print(f"Error fetching trading pairs: {e}")
            raise e

    def get_history_candles(self, symbol, timeframe, limit=100):
        pass

    def market_and_account_data(self, symbol: str, intervals: List[str], limit: int = 500) -> dict:
        pass
