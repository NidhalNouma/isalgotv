import requests
import random
import string

from django.utils.dateparse import parse_datetime

import environ
env = environ.Env()
meta_api_token = env('META_API_TOKEN')

from automate.functions.brokers.types import *
from automate.functions.brokers.broker import BrokerClient

class MetatraderClient(BrokerClient):
    api_url = "https://mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai"
    api_data_url = "https://mt-client-api-v1.new-york.agiliumtrade.ai"
    api_market_data_url = "https://mt-market-data-client-api-v1.new-york.agiliumtrade.ai"

    def generate_random_string(self, length):
        """Generate a random alphanumeric string of the given length."""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=length))
        
    def get_mt_profile_by_server_name(self, server_name, version):
        """
        Check MT profiles for the provided server name.
        
        Args:
            server_name (str): The server name to search in.
            version (str): "mt4" or other (for mt5).
        
        Returns:
            dict: On success, returns a dict with {"valid": True, "id": profile_id}.
                On failure, returns {"error": error_message}.
        """
        print("Checking MT profiles for server ...", server_name)
        v = 4 if version == "mt4" else 5
        url = f"{self.api_url}/users/current/provisioning-profiles?version={v}"
        headers = {
            "auth-token": meta_api_token
        }
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if isinstance(data, list):
                result = {"valid": True, "id": ""}
                for item in data:
                    profile_name = item.get("name", "")
                    # Check if profile_name is found in server_name
                    if profile_name in server_name:
                        result["id"] = item.get("_id", "")
                        break
                return result
            else:
                if data.get("error"):
                    if data.get("id"):
                        print(data)
                    return {"error": data.get("message")}
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}

    def __init__(self, account=None, current_trade=None):
        if account:
            self.account = account
            self.account_api_id = account.account_api_id
        else:
            pass

        self.current_trade = current_trade

    @staticmethod
    def check_credentials(account_name, account_number, account_password, account_server, account_type, profile_id=""):
        """
        Add a new MT API account.
        
        Args:
            account_name (str): The name for the account.
            account_number (str/int): The account number (login).
            account_password (str): The account password.
            account_server (str): The server for the account.
            account_type (str): "mt4" or other (for mt5).
            profile_id (str, optional): The provisioning profile id. Defaults to "".
        
        Returns:
            dict: API response data or error message.
        """
        print("Adding new MT API account ...")
        client = MetatraderClient()
        transaction_id = client.generate_random_string(32)
        
        # If profile_id is not provided, fetch it based on the server name.
        if not profile_id:
            pr = client.get_mt_profile_by_server_name(account_server, account_type)
            if pr.get("valid") and pr.get("id"):
                profile_id = pr["id"]
            print("profileId:", profile_id)
        
        url = f"{client.api_url}/users/current/accounts"
        payload = {
            "login": account_number,
            "password": account_password,
            "name": account_name,
            "server": account_server,
            "platform": account_type,
            "region": "new-york",
            'type': "cloud-g2", # cloud-g2 or cloud-g1 for higher performance (costs more)
            "manualTrades": True,
            "metastatsApiEnabled": False,
            "magic": 0,
            "provisioningProfileId": profile_id,
        }
        headers = {
            "auth-token": meta_api_token,
            "transaction-id": transaction_id,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            print(data)
            if data.get("error"):
                if data.get("id"):
                    print(data)
                return {"error": data.get("message"),  "valid": False}
            
            data["valid"] = True
            data["account_api_id"] = data.get("id", "")
            data["account_type"] = 'demo' if 'demo' in str(data.get("server", "")).lower() else 'live'
            return data
        except Exception as e:
            print("Error:", e)
            return {"error": str(e), "valid": False}

        
    def deploy_undeploy_account(self, deploy = True):
        """
        Deploy/Undeploy an MT API account.
        Args:
            account (object): The account object containing account_api_id.
            deploy (bool): True to deploy, False to undeploy.
        Returns:
            dict: API response data or error message.
        """

        print("Deploy/Undeploy  MT API account ...")


        
        url = f"{self.api_url}/users/current/accounts/{self.account_api_id}/deploy"
        if not deploy:
            url = f"{self.api_url}/users/current/accounts/{self.account_api_id}/undeploy"

        payload = {
            "executeForAllReplicas": True,
        }
        headers = {
            "auth-token": meta_api_token,
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 204:
                print("Account deployed successfully.")
                return {"message": "Account deployed successfully."}
            else:
                data = response.json()
                raise Exception(data.get("message", "Failed to deploy/undeploy account."))
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}

    def delete_account(self):
        """
        Delete an MT API account.
        
        Args:
            account_api_id (str): The account API id to delete.
        
        Returns:
            dict: API response data or error message.
        """

        print("Deleting account API ...", self.account_api_id)


        url = f"{self.api_url}/users/current/accounts/{self.account_api_id}"
        headers = {
            "auth-token": meta_api_token
        }
        
        try:
            response = requests.delete(url, headers=headers)

            if response.status_code == 204:
                print("Account deleted successfully.")
                return {"message": "Account deleted successfully."}
            else:
                data = response.json()
                raise Exception(data.get("message", "Failed to delete account."))
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}
            
    def get_account_information(self):
        """
        Get account information for a given account API id.
        
        Args:
            account_api_id (str): The account API id.
        
        Returns:
            dict: Account information data or error message.
        """
        print("Getting account information ...", self.account_api_id)
        url = f"{self.api_data_url}/users/current/accounts/{self.account_api_id}/account-information"
        headers = {
            "auth-token": meta_api_token
        }
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            if data.get("error"):
                return {"error": data.get("message")}
            return data
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}
    
        
    def get_trade_currency(self):
        try:
            acc = self.get_account_information()
            currency = acc.get('currency', None)
            return currency
        except Exception as e:
            return None
    

    def open_trade(self, symbol, action_type:str, lot_size, custom_id=''):
        """
        Opens a trade for the given account.

        Args:
            account_api_id (str): The account API id.
            client_id (str/int): A client-provided id.
            action_type (str): "buy" or "sell".
            symbol (str): Trading symbol.
            lot_size (float): Base volume.
        Returns:
            dict: Response from the API or error details.
        """
        account_api_id = self.account_api_id 
        print("Open a trade ...", account_api_id)
        try:
            if action_type.lower() == "buy":
                position_type = "ORDER_TYPE_BUY"
            elif action_type.lower() == "sell":
                position_type = "ORDER_TYPE_SELL"
            else:
                position_type = ""

            url = f"{self.api_data_url}/users/current/accounts/{account_api_id}/trade"

            payload = {
                "actionType": position_type,
                "symbol": symbol,
                "volume":  round(float(lot_size), 2),
                "clientId": 'I_S_' + str(self.account.id),
            }

            headers = {
                "auth-token": meta_api_token,
            }

            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            # print("Response status code:", response, data)

            order_id = data.get("orderId")

            open_price = data.get("price", "0")
            open_time = ''

            trade_data = self.get_order_info(symbol, order_id)
            if trade_data:
                open_price = trade_data.get("price", 0)
                open_time = parse_datetime(trade_data.get('time', ''))

                # print(open_price, ' .  ', open_time)

            currency = self.get_trade_currency()


            if not order_id:
                error_message = data.get("message", "Failed to open trade.")
                return {"error": error_message}
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': order_id,
                'symbol': symbol,
                'price': open_price,
                'time': open_time,
                'qty': lot_size,
                'currency': currency if currency else '',
            }

        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}


    def close_trade(self, symbol, order_type, partial_close=0):
        """
        Closes a trade for a given account.

        Args:
            account_api_id (str): The account API id.
            trade_id (str): The trade id to be closed.
            partial_close_percentage (float, optional): Percentage for partial close (0-100).
            partial_close (float, optional): Volume to close partially if applicable.

        Returns:
            dict: API response data or error details.
        """

        partial_close = max(float(partial_close), 0.01)
        partial_close = round(float(partial_close), 2)

        trade = self.current_trade

        account_api_id = self.account_api_id 
        print("Close a trade ...", account_api_id, trade.order_id)
        
        # Prepare the payload data.
        data = {
            "actionType": "POSITION_PARTIAL",
            "positionId": trade.order_id,
            "volume": partial_close,
       }

        url = f"{self.api_data_url}/users/current/accounts/{account_api_id}/trade"
        headers = {
            "auth-token": meta_api_token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            resp_data = response.json()
            if resp_data.get("error"):
                return {"error": resp_data.get("message")}
            else:
                return {
                    'message': f"Trade closed for order ID {id}.", 
                    "order_id": trade.order_id,
                    'qty': partial_close,
                }
                # return resp_data
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}
        
        
    def get_order_info(self, symbol, trade_id) -> OrderInfo:
            # Prepare the payload data.
        data = {
            "actionType": "POSITION_PARTIAL",
            "positionId": trade_id,
        }

        url = f"{self.api_data_url}/users/current/accounts/{self.account_api_id}/history-deals/position/{trade_id}"

        headers = {
            "auth-token": meta_api_token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, json=data, headers=headers)
            if response.status_code != 200:
                raise Exception("Error getting trade data ,")
            else:
                resp_data = response.json()
                
                if isinstance(resp_data, list) and resp_data:
                    last_trade = resp_data[-1]

                if last_trade:
                    res = {
                        'order_id':trade_id ,
                        'symbol': str(last_trade.get('symbol')),
                        'volume': str(last_trade.get('volume')),
                        # 'side': str(trade.side),

                        'price': str(last_trade.get('price')),

                        'time': str(parse_datetime(last_trade.get('time'))), 

                        
                        'fees': str(abs(float(last_trade.get('commission') or 0)) + abs(float(last_trade.get('swap') or 0))), 
                        'profit': str(last_trade.get('profit')),

                        'additional_info': {
                            'commission': str(last_trade.get('commission')),
                            'swap': str(last_trade.get('swap')),
                            'broker_time': str(parse_datetime(last_trade.get('brokerTime'))),
                        }
                    }

                    # if not trade.currency:
                    #     currency = get_trade_currency(account)
                    #     if currency:
                    #         res['currency'] = currency

                    return res
                
            return None
            
        except Exception as e:
            print('get_trade_date ', e)
            return None

    def get_symbol_info(self, symbol):
        try:
            url = f"{self.api_data_url}/users/current/accounts/{self.account_api_id}/symbols/{symbol}/specification"
            headers = {
                "auth-token": meta_api_token
            }
            response = requests.get(url, headers=headers)
            data = response.json()
            if data.get("error"):
                return None
            return data
        except Exception as e:
            print("Error:", e)
            return None
        
    def get_account_balance(self, symbol = None):
        try:
            url = f"{self.api_data_url}/users/current/accounts/{self.account_api_id}/account-information"
            headers = {
                "auth-token": meta_api_token
            }
            response = requests.get(url, headers=headers)
            data = response.json()
            if data.get("error"):
                return {"error": data.get("message")}
            
            balance = float(data.get("balance", 0))
            equity = float(data.get("equity", 0))
            margin = float(data.get("margin", 0))
            free_margin = float(data.get("freeMargin", 0))
            currency = data.get("currency", "")
            
            return {
                "balance": balance,
                "equity": equity,
                "margin": margin,
                "free_margin": free_margin,
                "currency": currency,
            }
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}
        
    def get_history_candles(self, symbol, interval, limit = 500):
        try:
            if interval not in ["1m", "2m", "3m", "4m", "5m", "6m", "10m", "12m", "15m", "20m", "30m", "1h", "2h", "3h", "4h", "6h", "8h", "12h", "1d", "1w", "1mn"]:
                return {"error": "Invalid interval. Supported intervals: 1m, 2m, 3m, 4m, 5m, 6m, 10m, 12m, 15m, 20m, 30m, 1h, 2h, 3h, 4h, 6h, 8h, 12h, 1d, 1w, 1mn."}

            if limit > 1000:
                limit = 1000
            url = f"{self.api_market_data_url}/users/current/accounts/{self.account_api_id}/historical-market-data/symbols/{symbol}/timeframes/{interval}/candles"

            headers = {
                "auth-token": meta_api_token
            }
            response = requests.get(url, headers=headers, params={"limit": limit})
            data = response.json()
            
            if isinstance(data, list):
                candles = []
                for item in data:
                    candle = {
                        "time": parse_datetime(item.get("time")),
                        "open": float(item.get("open", 0)),
                        "high": float(item.get("high", 0)),
                        "low": float(item.get("low", 0)),
                        "close": float(item.get("close", 0)),
                        "volume": float(item.get("volume", 0)),
                    }
                    candles.append(candle)
                    
                return candles

            if data.get("error"):
                return {"error": data.get("message")}
            
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}
        
    def get_trading_pairs(self):
        try:
            url = f"{self.api_data_url}/users/current/accounts/{self.account_api_id}/symbols"
            headers = {
                "auth-token": meta_api_token
            }
            response = requests.get(url, headers=headers)
            data = response.json()

            if isinstance(data, list):
                return data
            if data.get("error"):
                return {"error": data.get("message")}

        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}
        
    def get_current_price(self, symbol):
        try:
            url = f"{self.api_data_url}/users/current/accounts/{self.account_api_id}/symbols/{symbol}/current-price"
            headers = {
                "auth-token": meta_api_token
            }
            response = requests.get(url, headers=headers)
            data = response.json()
            if data.get("error"):
                return {"error": data.get("message")}
            
            bid = float(data.get("bid", 0))
            ask = float(data.get("ask", 0))
            
            return {
                "bid": bid,
                "ask": ask,
            }
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}
        
    def market_and_account_data(self, symbol, intervals, limit = 500):
        try:
            history_candles = {}
            for interval in intervals:
                candles = self.get_history_candles(symbol, interval, limit)
                if isinstance(candles, dict) and candles.get("error"):
                    return {"error": candles.get("error")}
                history_candles[interval] = candles
            
            account_data = self.get_account_balance()
            symbol_info = self.get_symbol_info(symbol)
            current_price = self.get_current_price(symbol)
            
            
            return {
                "history_candles": history_candles,
                "account_info": account_data,
                "symbol_info": symbol_info,
                "current_price": current_price,
            }
        except Exception as e:
            print("Error:", e)
            return {"error": str(e)}
