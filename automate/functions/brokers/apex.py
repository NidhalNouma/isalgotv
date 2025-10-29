# from apexomni.constants import APEX_HTTP_MAIN, APEX_OMNI_HTTP_TEST
# from apexomni.http_private_v3 import HttpPrivate_v3
# from apexomni.http_public import HttpPublic

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

class ApexClient(CryptoBrokerClient):
    pass
    # def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):

    #     super().__init__(account=account, api_key=api_key, api_secret=api_secret, passphrase=passphrase , account_type=account_type, current_trade=current_trade)

    #     self.private_client = HttpPrivate_v3(
    #             endpoint=APEX_HTTP_MAIN,
    #             api_key_credentials={'key': api_key, 'secret': api_secret, 'passphrase': passphrase},
    #         )
    #     self.public_client = HttpPublic(APEX_HTTP_MAIN)
