import requests
import json
import uuid
from bs4 import BeautifulSoup

from .broker import BrokerClient
from .types import *


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

        self.csrf = ""
        self.API_URL = f"https://demo.dx.trade"
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
        """
        1) POST /api/auth/login  with {"username","password","vendor"}
        2) On HTTP 200: store cookies in self.cookies, then call self.fetch_csrf()
        3) Optionally fetch positions (or accounts) to verify login success
        """
        url = f"{self.API_URL}/dxsca-web/login"
        payload = {
            "username": self.username,
            "password": self.password,
            "domain": self.server
        }
        print(payload)
        headers = {
            "Content-Type": "application/json"
        }

        resp = self.s.post(url, headers=headers, data=json.dumps(payload))
        print(resp)
        if resp.status_code != 200:
            raise Exception(f"Login failed: HTTP {resp.status_code} - {resp.text}")

        # Save each cookie into self.cookies
        for cookie in resp.cookies:
            self.cookies[cookie.name] = cookie.value

        # Fetch CSRF token from the landing page
        token = self.fetch_csrf()
        if not token:
            raise Exception("Login succeeded but failed to retrieve CSRF token.")

        # (Optional) Fetch account info immediately to confirm
        self.get_account_info()

    def fetch_csrf(self):
        """
        GET /  (with only JSESSIONID in cookies)  → parse <meta name="csrf" content="..."> 
        Saves self.csrf and returns it.
        """
        # Only send JSESSIONID (or any name containing "JSESSIONID")
        cookies_in_req = {k: v for k, v in self.cookies.items() if "JSESSIONID" in k}

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;"
                      "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.7",
            "Cookie": "; ".join([f"{k}={v}" for k, v in cookies_in_req.items()])
        }

        resp = self.s.get(self.API_URL, headers=headers, cookies=cookies_in_req)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        meta = soup.find("meta", attrs={"name": "csrf"})
        if meta and "content" in meta.attrs:
            self.csrf = meta["content"]
            return self.csrf

        return None

    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = "") -> OpenTrade:
        """
        POST /api/orders/single
        Headers:
          Content-Type: application/json; charset=UTF-8
          Cookie: all session cookies joined by "; "
          X-CSRF-Token: self.csrf
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
            "Cookie": "; ".join([f"{k}={v}" for k, v in self.cookies.items()]),
            "X-CSRF-Token": self.csrf,
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
          Cookie: all session cookies joined by "; "
          X-CSRF-Token: self.csrf
          X-Requested-With: XMLHttpRequest

        Returns the JSON‐decoded account info (balance, equity, etc.)
        """
        url = f"{self.API_URL}/api/accounts"
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Cookie": "; ".join([f"{k}={v}" for k, v in self.cookies.items()]),
            "X-CSRF-Token": self.csrf,
            "X-Requested-With": "XMLHttpRequest"
        }

        resp = self.s.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch account info: HTTP {resp.status_code} - {resp.text}")

        print(resp.json())

        return resp.json()
    

    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        pass
    

    def get_order_info(self, symbol, order_id) -> OrderInfo:
        pass