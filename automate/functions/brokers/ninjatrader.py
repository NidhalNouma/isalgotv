import requests
import json
import uuid

from automate.functions.brokers.broker import BrokerClient
from automate.functions.brokers.types import *


class NinjatraderClient(BrokerClient):

    def __init__(self, account=None, username=None, password=None, cid=None, type=None, current_trade=None):
        super().__init__()

        if account:
            self.username = account.username
            self.password = account.password
            self.cid = account.server
            self.type = account.type
        else:
            self.username = username
            self.password = password
            self.cid = cid
            self.type = type

        if self.type == 'L':
            self.API_URL = f"https://live.tradovateapi.com/v1"
        else:
            self.API_URL = f"https://demo.tradovateapi.com/v1"
        self.accessToken = None

        self.s = requests.Session()
        self.current_trade = current_trade

        self.login()


    @staticmethod
    def check_credentials(username, password, cid, type):
        """
        Tries to log in with the given credentials. Returns {"error": str, "valid": False} on failure.
        """
        try:
            client = NinjatraderClient(username=username, password=password, cid=cid, type=type)
            return {"error": None, "valid": True}
        except Exception as e:
            return {"error": str(e), "valid": False}
        

    def login(self):
        url = f"{self.API_URL}/auth/accesstokenrequest"
        payload = {
            "name": self.username,
            "password": self.password,
            # "cid": self.cid
        }
        print(payload)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        resp = self.s.post(url, headers=headers, data=json.dumps(payload))
        if resp.status_code != 200:
            raise Exception(f"Login failed: HTTP {resp.status_code} - {resp.text}")
        
        data = resp.json()
        print(data)

        if data.get('errorText'):
            raise Exception(data.get('errorText'))
        
        if data.get('accessToken'):
            self.accessToken = data.get('accessToken')
            return True
        else:
            raise Exception('Failed to login to this account. please try again later.')
        
        

    def open_trade(self, symbol: str, side: str, quantity: float, custom_id: str = "") -> OpenTrade:
        pass


    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        pass
    

    def get_order_info(self, symbol, order_id) -> OrderInfo:
        pass