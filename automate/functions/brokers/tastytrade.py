from tastytrade_sdk import Tastytrade

from automate.functions.brokers.broker import BrokerClient
from automate.functions.brokers.types import *


class TastytradeClient(BrokerClient):
    def __init__(self, account=None, username=None, password=None, server=None, type='L', current_trade=None):
        self.symbols_cache = {}
        self.current_trade = current_trade
        self.account_currency = self.current_trade.currency if self.current_trade else None

        if account:
            self.api_key = account.username
            self.api_secret = account.password
            self.refresh_token = account.server
        else:
            self.api_key = username
            self.api_secret = password
            self.refresh_token = server
        
        self.tasty = Tastytrade(
            client_id = self.api_key,
            client_secret = self.api_secret,
            refresh_token = self.refresh_token,
        )

        self.tasty.login(self.api_key, self.api_secret)