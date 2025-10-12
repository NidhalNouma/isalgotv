import requests
import json
import uuid
from bs4 import BeautifulSoup

from automate.functions.brokers.broker import BrokerClient
from automate.functions.brokers.types import *


class DxtradeClient(BrokerClient):
    def __init__(self, account=None, username=None, password=None, server=None, current_trade=None):
        super().__init__()

        if account:
            self.username = account.username
            self.password = account.password
            self.server = account.server
        else:
            self.username = username
            self.password = password
            self.server = server

        self.session_token = None
        self.API_URL = f"https://{self.server}"
        self.account_id = None
        self.cookies = {}
        self.s = requests.Session()

        self.current_trade = current_trade

    @staticmethod
    def check_credentials(username, password, server):
        """
        Tries to log in with the given credentials. Returns {"error": str, "valid": False} on failure.
        """
        try:
            client = DxtradeClient(username=username, password=password, server=server)
            client.login()
            return {"error": None, "valid": True}
        except Exception as e:
            return {"error": str(e), "valid": False}

    def login(self):
        url = f"{self.API_URL}/api/auth/login"
        payload = {
            "username": self.username,
            "password": self.password,
            "domain": 'default',
            # "domain": self.server.split('.')[1],
            # "vendor": "mercury",
        }
        
        print(payload)
        headers = {
            "Content-Type": "application/json",
        }

        resp = self.s.post(url, headers=headers, data=json.dumps(payload))
        print(resp.text)

        if resp.status_code != 200:
            raise Exception(f"Login failed: HTTP {resp.status_code} - {resp.text}")
        
        resp_json = resp.json()
        # After login
        for cookie in resp.cookies:
            self.cookies[cookie.name] = cookie.value

        if "JSESSIONID" in self.cookies:
            session_id = self.cookies["JSESSIONID"]
            print(f"JSESSIONID: {session_id}")
        else:
            print("Warning: no JSESSIONID cookie found.")

        accounts = self.get_account_transactions()

        print(accounts)
        
        
        # #Try to fetch token from /api/auth/session
        # session_resp = self.s.get(f"{self.API_URL}/api/auth/state")
        # print("Session info:", session_resp.text)

        # session_data = session_resp.json()

        # print(session_data)


        if resp_json.get('loginStatusTO', {}).get('statusCode'):
            raise Exception(resp_json.get('loginStatusTO').get('statusCode'))
        else:

            return True

    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = "") -> OpenTrade:
        """
        POST /api/orders/single
        Headers:
          Content-Type: application/json; charset=UTF-8
          Authorization: DXAPI <sessionToken>
          X-Requested-With: XMLHttpRequest

        Body (no spaces in JSON):
        {
          "directExchange": false,
          "legs": [
            {
              "instrumentId": symbol,
              "positionEffect": "OPENING",
              "ratioQuantity": 1,
              "symbol": symbol
            }
          ],
          "orderSide": "BUY" or "SELL",
          "quantity": quantity,
          "requestId": "gwt-uid-931-" + uuid4(),
          "timeInForce": "GTC"
        }
        """
        url = f"{self.API_URL}/api/orders/single"
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Authorization": f"DXAPI {self.session_token}",
            "X-Requested-With": "XMLHttpRequest"
        }

        body = {
            "directExchange": False,
            "legs": [
                {
                    "instrumentId": symbol,
                    "positionEffect": "OPENING",
                    "ratioQuantity": 1,
                    "symbol": symbol
                }
            ],
            "orderSide": "BUY" if side.strip().upper() == "BUY" else "SELL",
            "quantity": quantity,
            "requestId": f"gwt-uid-931-{uuid.uuid4()}",
            "timeInForce": "GTC"
        }

        # The API expects compact JSON with no extra spaces
        compact_json = json.dumps(body, separators=(",", ":"))
        resp = self.s.post(url, headers=headers, data=compact_json)
        if resp.status_code != 200:
            raise Exception(f"Open trade failed: HTTP {resp.status_code} - {resp.text}")

        return OpenTrade(**resp.json())


    def get_account_info(self) -> dict:
        """
        GET /api/accounts
        Headers:
          Content-Type: application/json; charset=UTF-8
          Authorization: DXAPI <sessionToken>
          X-Requested-With: XMLHttpRequest

        Returns the JSON‐decoded account info (balance, equity, etc.)
        """
        url = f"{self.API_URL}/api/accounts"
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            # "Authorization": f"DXAPI {self.session_token}",
            "Cookie": f"JSESSIONID={self.session_token}",
            "X-Requested-With": "XMLHttpRequest"
        }

        resp = self.s.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch account info: HTTP {resp.status_code} - {resp.text}")

        print(resp.json())

        return resp.json()
    

    def get_final_trade_details(self, trade, order_id=None):
        pass
    

    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        pass

    def get_order_info(self, symbol, order_id) -> OrderInfo:
        pass

    def get_account_balance(self, symbol = None):
        pass
    
    def get_current_price(self, symbol):
        pass
    
    def get_trading_pairs(self):
        pass
    
    def get_history_candles(self, symbol, interval, limit = 500):
        pass

    def market_and_account_data(self, symbol, intervals, limit = 500):
        pass