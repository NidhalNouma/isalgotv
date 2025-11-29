import time
import requests

from automate.functions.brokers.broker import BrokerClient
from automate.functions.brokers.types import *


class TastytradeClient(BrokerClient):
    def __init__(self, account=None, username=None, password=None, server=None, type='L', account_id=None, current_trade=None):
        self.s = requests.Session()
        self.accessToken = None
        self.symbols_cache = {}
        self.current_trade = current_trade

        self.account_currency = self.current_trade.currency if self.current_trade else None

        self.remember_me_token = None

        if account:
            self.username = account.username
            self.password = account.password
            self.account_number = account.account_api_id if account.account_api_id else None
            self.type = account.type
            self.remember_me_token = account.additional_info.get('remember_me_token') if account.additional_info else None
        else:
            self.username = username
            self.password = password
            self.account_number = account_id
            self.type = type

        self.API_URL = "https://api.tastytrade.com"
        if self.type.lower() in ['d', 'demo']:
            self.API_URL = "https://api.cert.tastyworks.com"

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
                if client.remember_me_token:
                    additional_info = {'remember_me_token': client.remember_me_token}
                    
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
                "login": self.username,
                "password": self.password,
                "remember-me": True
            }
            # if self.remember_me_token:
            #     login_data["remember-token"] = self.remember_me_token
            #     login_data.pop("password", None)  # Remove password if remember-me-token is used

            response = self._send_request("POST", "/sessions", data=login_data, with_auth_header=False, max_retries=1)
            data = response.get("data", {})
            if data.get("error"):
                raise Exception(f"Login failed: {data.get('error')}")
            self.accessToken = data.get("session-token")
            self.remember_me_token = data.get("remember-token")
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
        return self.get_account_info()

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

            response = self._send_request("POST", f"/accounts/{self.account_number}/orders/dry-run", data=data, max_retries=1)
            end_exe = time.perf_counter()
            if response.get("error"):
                raise Exception(response.get('error'))
            order_data = response.get("data", {})
            print(f"Trade opened successfully for {symbol}: {order_data}")
            return order_data
        except Exception as e:
            print(f"Error opening trade for {symbol}: {e}")
            raise e

    def close_trade(self, symbol, side, quantity):
        pass

    def get_order_info(self, symbol, order_id):
        pass

    def get_trading_pairs(self):
        pass

    def get_history_candles(self, symbol, timeframe, limit=100):
        pass

    def market_and_account_data(self, symbol: str, intervals: List[str], limit: int = 500) -> dict:
        pass
