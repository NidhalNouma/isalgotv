import requests
from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from twisted.internet import reactor


from automate.functions.brokers.broker import BrokerClient

class CtraderClient(BrokerClient):




    def login(username: str, password: str, client_id: str, client_secret: str):
        token_url = "https://connect.spotware.com/apps/token"

        payload = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "trade"
        }

        response = requests.post(token_url, data=payload)
        tokens = response.json()
        print(tokens)
