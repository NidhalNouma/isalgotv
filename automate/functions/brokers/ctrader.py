import requests
import uuid
import threading
import datetime, calendar
from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from google.protobuf.json_format import MessageToDict


from twisted.internet import reactor, task, defer, threads
from twisted.internet.defer import Deferred

from django.conf import settings
from django.urls import reverse

from automate.models import ForexBrokerAccount
from automate.functions.brokers.broker import BrokerClient

import environ
env = environ.Env()

CLIENT_ID = env('CTRADER_CLIENT_ID')
CLIENT_SECRET = env('CTRADER_SECRET_KEY')

def onProtoOAApplicationAuthRes(result):
    print(result)

def onError(failure):
    print(failure)


def disconnected(client, reason): # Callback for client disconnection
    print("\nCtrader Disconnected: ", reason)

def onMessageReceived(client, message): # Callback for receiving all messages
    print("Message received: \n( ", Protobuf.extract(message), " )")

def connected(client): # Callback for client connection
    print("\nCtrader Connected")
    # Now we send a ProtoOAApplicationAuthReq
    request = ProtoOAApplicationAuthReq()
    request.clientId = CLIENT_ID
    request.clientSecret = CLIENT_SECRET
    # Client send method returns a Twisted deferred
    deferred = client.send(request)
    # You can use the returned Twisted deferred to attach callbacks
    # for getting message response or error backs for getting error if something went wrong
    # deferred.addCallbacks(onProtoOAApplicationAuthRes, onError)
    deferred.addErrback(onError)

d_client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
l_client = Client(EndPoints.PROTOBUF_LIVE_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)

# Setting optional client callbacks
d_client.setConnectedCallback(connected)
d_client.setDisconnectedCallback(disconnected)
d_client.setMessageReceivedCallback(onMessageReceived)
# Starting the client service
d_client.startService()

# # Setting optional client callbacks
# l_client.setConnectedCallback(connected)
# l_client.setDisconnectedCallback(disconnected)
# l_client.setMessageReceivedCallback(onMessageReceived)
# # Starting the client service
# l_client.startService()

# Run Twisted reactor
def start_reactor_in_background():
    if not reactor.running:
        thread = threading.Thread(
            target=lambda: reactor.run(installSignalHandlers=False),
            daemon=True
        )
        thread.start()
start_reactor_in_background()

def parse_payload(payload):
    if hasattr(payload, "payload"):
        try:
            # Try to parse the ProtoOAGetAccountListByAccessTokenRes
            parsed = Protobuf.extract(payload)
            # print('📥 Decoded payload => ', payload)
            payload = parsed
        except Exception as e:
            print("⚠️ Failed to decode payload:", e)

    return payload
    

class CtraderClient(BrokerClient):

    def __init__(self, account=None, authorization_code=None, type: str = 'demo'):
        
        self.type = type
        self.port = EndPoints.PROTOBUF_PORT
        self.host = EndPoints.PROTOBUF_LIVE_HOST if type.lower() == "l" else EndPoints.PROTOBUF_DEMO_HOST
        
        self.account_id = None
        if account: 
            authorization_code = account.server
            self.account_id = int(account.username)
            self._id = account.id

        
        tokens = self.get_access_token(authorization_code)
        self.access_token = tokens.get('access_token')
        self.refresh_token = tokens.get('refresh_token')
        self.tokens = f'{self.access_token}||{self.refresh_token}'

        self.symbols = set()
        
        if not self.account_id:
            acc = self.get_first_account()
            self.account_id = acc.get('account_id', None)
            self.type = 'live' if acc.get('is_live', False) else 'demo'

        self.authorize_account()
        print('✅ Account ID set to', self.account_id)

    @property
    def client(self):
        return d_client

    def close(self):
        if self._id:
            account = ForexBrokerAccount.objects.get(id=self._id)
            if account:
                account.server = self.tokens
                account.save(update_fields=["server"])
                print('Ctrader Auth key updated! ', self._id)
    
    @staticmethod
    def check_credentials(authorization_code: str, type: str):
        try:
            client = CtraderClient(authorization_code=authorization_code, type=type)

            if client:
                return {
                    "error": None, 
                    "valid": True, 
                    "ctrader_access_token": client.tokens,
                    "account_id": client.account_id,
                    "account_type": client.type,
                }
            else:
                raise Exception('Access denied. Credentials are not valid.')

        except Exception as e:
            return {"error": str(e), "valid": False}

    def get_access_token(self, code):
        try:
            codes = code.split('||')

            code = codes[0]
            refresh_token = codes[1] if len(codes) > 1 else None
            
            if refresh_token:
                data = {
                    "grant_type": "refresh_token",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "refresh_token": refresh_token,
                }
            else:
                scheme = "http" if ("local" in settings.PARENT_HOST or "127" in settings.PARENT_HOST) else "https"
                redirect_url = f"{scheme}://{settings.PARENT_HOST}{reverse('ctrader_auth_code')}"
                data = {
                    "grant_type": "authorization_code",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_url
                }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}


            # print(data)
            response = requests.post(url=EndPoints.TOKEN_URI, data=data, headers=headers)
            response.raise_for_status()
            res_json =  response.json()

            # print('response ' ,res_json)
            if res_json.get('errorCode', None):
                raise Exception(res_json.get('description', 'Error ocuured please try again!'))
            elif res_json.get('accessToken', None):
                return {
                    'access_token': res_json.get('accessToken'),
                    'expires_in': res_json.get('expiresIn'),
                    'refresh_token': res_json.get('refresh_token')
                }
        
        except Exception as e:
            raise Exception(str(e))
        
    def get_first_account(self):
        """
        Returns the first ctidTraderAccountId associated with the access token.
        Raises an Exception if no trading accounts are found.
        """
        def run():
            d = defer.Deferred()

            def on_account_list(result):
                result = parse_payload(result)
                if hasattr(result, "ctidTraderAccount") and len(result.ctidTraderAccount) > 0:
                    account = result.ctidTraderAccount[0]
                    account_id = account.ctidTraderAccountId
                    is_live = account.isLive
                    login = account.traderLogin
                    d.callback({
                        'account_id': account_id,
                        'is_live': is_live,
                        'login': login,
                    })
                else:
                    d.errback(Exception("No trading account found."))

            account_list_req = ProtoOAGetAccountListByAccessTokenReq()
            account_list_req.accessToken = self.access_token
            self.client.send(account_list_req).addCallback(on_account_list).addErrback(d.errback)
            return d

        account = threads.blockingCallFromThread(reactor, run)
        return account


    def authorize_account(self):
        """
        Authorizes the trading account using ProtoOAAccountAuthReq.
        Sends the authorization request with self.account_id and self.access_token via self.client.
        Uses Twisted Deferreds to handle asynchronous response and makes it synchronous with threads.blockingCallFromThread.
        On success, prints a success message and returns True; on failure, raises an Exception with the error message.
        """
        def run():
            d = defer.Deferred()

            def on_success(_):
                print("✅ Account authorized successfully.")
                d.callback(True)

            def on_failure(failure):
                error_msg = str(failure.value) if hasattr(failure, "value") else str(failure)
                raise Exception(f"Account authorization failed: {error_msg}")

            auth_req = ProtoOAAccountAuthReq()
            auth_req.ctidTraderAccountId = self.account_id
            auth_req.accessToken = self.access_token
            self.client.send(auth_req).addCallback(on_success).addErrback(d.errback)
            return d

        try:
            result = threads.blockingCallFromThread(reactor, run)
            return result
        except Exception as e:
            raise Exception(f"Account authorization failed: {e}")

    def get_account_balance(self):
        """
        Requests and returns the account balance for the current account_id.
        Assumes the account is already authorized.
        """
        def run():
            d = defer.Deferred()
            print(f"Requesting balance for account ID: {self.account_id}")
            info_req = ProtoOATraderReq()
            info_req.ctidTraderAccountId = self.account_id

            def on_info(info):
                info = parse_payload(info)
                print("📊 Trader info:", info)
                if hasattr(info, "trader") and hasattr(info.trader, "balance"):
                    d.callback(info.trader.balance)
                else:
                    d.errback(Exception("Balance not found."))

            self.client.send(info_req).addCallback(on_info).addErrback(d.errback)
            return d

        balance = threads.blockingCallFromThread(reactor, run)
        return balance
    
    def open_trade(self, symbol, action_type: str, lot_size, custom_id=''):
        """
        Opens a new trade (market order) using ProtoOASendOrderReq.
        Returns the order details or an error message.
        """

        try:
            # Get symbol ID
            symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)

            # Determine BUY or SELL
            side = ProtoOATradeSide.BUY if action_type.lower() in ["buy", "long"] else ProtoOATradeSide.SELL

            # Convert lot size to volume (1 lot = 100,000 units)
            volume = int(float(lot_size) * 100000)

            # Unique client order ID
            client_order_id = custom_id if custom_id else str(uuid.uuid4())[:12]

            def run():
                d = defer.Deferred()

                def on_order_response(response):
                    res = parse_payload(response)

                    # Handle normal order response
                    if hasattr(res, "order"):
                        order_info = MessageToDict(res.order, preserving_proto_field_name=True)
                        d.callback(order_info)
                        return

                    # Handle rejection
                    if hasattr(res, "errorCode"):
                        d.errback(Exception(f"Order rejected: {res.errorCode}"))
                        return

                    d.errback(Exception("Unknown response format from cTrader."))

                # Build and send order request
                req = ProtoOANewOrderReq()
                req.ctidTraderAccountId = self.account_id
                req.symbolId = int(symbol_id)
                req.orderType = ProtoOAOrderType.MARKET
                req.tradeSide = side
                req.volume = volume
                req.clientOrderId = client_order_id

                self.client.send(req).addCallback(on_order_response).addErrback(d.errback)
                return d

            # Run synchronously
            result = threads.blockingCallFromThread(reactor, run)
            print(f"✅ Trade opened successfully: {result}")
            return result

        except Exception as e:
            print("❌ Error opening trade:", e)
            return {"error": str(e)}

        finally:
            self.close()

    def close_trade(self, symbol, order_type, partial_close=0):
        try:
            trade = self.current_trade

            symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)

            def run():
                d = defer.Deferred()

                def on_positions_response(response):
                    res = parse_payload(response)

                    if not hasattr(res, "position") or len(res.position) == 0:
                        d.errback(Exception("No open positions found."))
                        return

                    # Find the position for this symbol
                    position_to_close = None
                    for pos in res.position:
                        if pos.symbolId == symbol_id:
                            position_to_close = pos
                            break

                    if not position_to_close:
                        d.errback(Exception(f"No open position found for {symbol_name}."))
                        return

                    # Determine how much volume to close
                    total_volume = int(position_to_close.volume)
                    if partial_close > 0:
                        close_volume = int(float(partial_close) * 100000)
                        if close_volume > total_volume:
                            close_volume = total_volume
                    else:
                        close_volume = total_volume

                    # Build and send close request
                    def on_close_response(close_res):
                        close_res = parse_payload(close_res)
                        if hasattr(close_res, "position"):
                            position_info = MessageToDict(close_res.position, preserving_proto_field_name=True)
                            d.callback(position_info)
                        else:
                            d.errback(Exception("Failed to close position or invalid response."))

                    req = ProtoOAClosePositionReq()
                    req.ctidTraderAccountId = self.account_id
                    req.positionId = position_to_close.positionId
                    req.volume = close_volume

                    self.client.send(req).addCallback(on_close_response).addErrback(d.errback)

                # First, get all open positions
                positions_req = ProtoOAGetPositionsReq()
                positions_req.ctidTraderAccountId = self.account_id
                self.client.send(positions_req).addCallback(on_positions_response).addErrback(d.errback)
                return d

            result = threads.blockingCallFromThread(reactor, run)
            print(f"✅ Trade closed successfully: {result}")
            return result


        except Exception as e:
            print("❌ Error closing trade:", e)
            return {"error": str(e)}

        finally:
            self.close()
    
    def get_order_info(self, symbol, order_id):
        return super().get_order_info(symbol, order_id)
        
    def get_current_price(self, symbol):
        """
        Gets the current bid/ask price for a given symbol using ProtoOASubscribeSpotsReq.
        Returns: {"symbol_id", "symbol_name", "bid", "ask", "spread"}
        """
        symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)

        def run():
            d = defer.Deferred()

            def handle_message(client, message):
                msg = parse_payload(message)
                # Check if message is a ProtoOASpotEvent and matches our symbol
                if hasattr(msg, "symbolId") and msg.symbolId == symbol_id and hasattr(msg, "bid"):
                    bid = getattr(msg, "bid", None)
                    ask = getattr(msg, "ask", None)
                    if bid is not None and ask is not None:
                        spread = ask - bid
                        # Once we get the price, stop listening
                        self.client.setMessageReceivedCallback(onMessageReceived)
                        d.callback({
                            "symbol_id": symbol_id,
                            "symbol_name": symbol_name,
                            "bid": bid,
                            "ask": ask,
                            "spread": spread
                        })

            # Temporarily override the global message callback
            self.client.setMessageReceivedCallback(handle_message)

            # Send a subscribe request
            sub_req = ProtoOASubscribeSpotsReq()
            sub_req.ctidTraderAccountId = self.account_id
            sub_req.symbolId.append(symbol_id)
            self.client.send(sub_req).addErrback(d.errback)

            # Set timeout to revert callback if no response
            reactor.callLater(
                5, lambda: (not d.called and d.errback(Exception("Timeout waiting for spot event")))
            )

            return d

        try:
            result = threads.blockingCallFromThread(reactor, run)
            return result
        except Exception as e:
            raise Exception(f"Failed to get current price for '{symbol}': {e}")

    def get_current_price(self, symbol):
        """
        Gets the current bid/ask price for a given symbol using ProtoOASubscribeSpotsReq.
        Returns: {"symbol_id", "symbol_name", "bid", "ask", "spread"}
        """
        symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)

        def run():
            d = defer.Deferred()
            got_price = {"done": False}

            def on_spot_event(client, message):
                msg = Protobuf.extract(message)  # ✅ Use Protobuf.extract, not parse_payload
                if msg.DESCRIPTOR.name == "ProtoOASpotEvent":
                    if getattr(msg, "symbolId", None) == symbol_id and hasattr(msg, "bid") and hasattr(msg, "ask"):
                        bid = msg.bid
                        ask = msg.ask
                        spread = ask - bid
                        got_price["done"] = True

                        # ✅ Unsubscribe after receiving one event
                        unsub_req = ProtoOAUnsubscribeSpotsReq()
                        unsub_req.ctidTraderAccountId = self.account_id
                        unsub_req.symbolId.append(symbol_id)
                        self.client.send(unsub_req)

                        # ✅ Restore global callback only after unsubscribing
                        self.client.setMessageReceivedCallback(onMessageReceived)

                        d.callback({
                            "symbol_id": symbol_id,
                            "symbol_name": symbol_name,
                            "bid": bid,
                            "ask": ask,
                            "spread": spread
                        })

            # Temporarily override global message callback
            self.client.setMessageReceivedCallback(on_spot_event)

            # Send subscribe request
            sub_req = ProtoOASubscribeSpotsReq()
            sub_req.ctidTraderAccountId = self.account_id
            sub_req.symbolId.append(symbol_id)
            self.client.send(sub_req)

            # Timeout protection
            reactor.callLater(
                8, lambda: (
                    not d.called and d.errback(Exception("Timeout waiting for spot event")),
                    self.client.setMessageReceivedCallback(onMessageReceived)
                )
            )
            return d

        try:
            result = threads.blockingCallFromThread(reactor, run)
            # print(result)
            return result
        except Exception as e:
            raise Exception(f"Failed to get current price for '{symbol}': {e}")

    def get_history_candles(self, symbol, interval="1m", limit=500):
        """
        Fetches historical candle (trendbar) data for a given symbol and timeframe
        using ProtoOAGetTrendbarsReq. Returns OHLCV candles as dictionaries.
        """

        # Get symbol id and details
        symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)
        symbol_info = self.get_symbol_info(symbol_name)
        digits = int(symbol_info.get("digits", 5))

        # Map interval string to ProtoOATrendbarPeriod
        period_map = {
            "1m": "M1",
            "5m": "M5",
            "15m": "M15",
            "30m": "M30",
            "1h": "H1",
            "4h": "H4",
            "1d": "D1",
            "1w": "W1",
            "1M": "MN1",
        }

        if interval not in period_map:
            raise Exception(f"Unsupported interval '{interval}'")

        # Compute time range
        now = datetime.datetime.utcnow()
        # The API example uses weeks — we’ll compute based on limit and period
        if "m" in interval:
            delta = datetime.timedelta(minutes=limit)
        elif "h" in interval:
            delta = datetime.timedelta(hours=limit)
        elif "d" in interval:
            delta = datetime.timedelta(days=limit)
        elif interval == "1w":
            delta = datetime.timedelta(weeks=limit)
        else:
            delta = datetime.timedelta(days=limit * 30)  # 1M = 30 days approx

        start_time = int(calendar.timegm((now - delta).utctimetuple()) * 1000)
        end_time = int(calendar.timegm(now.utctimetuple()) * 1000)

        def run():
            d = defer.Deferred()

            def on_trendbars_response(response):
                res = parse_payload(response)

                if not hasattr(res, "trendbar") or len(res.trendbar) == 0:
                    d.errback(Exception("No trendbar data returned."))
                    return

                trendbars = []
                for tb in res.trendbar:
                    # Trendbar values are relative integers; must be adjusted
                    low = self.getPriceFromRelative(digits, tb.low)
                    high = self.getPriceFromRelative(digits, tb.low + tb.deltaHigh)
                    open_ = self.getPriceFromRelative(digits, tb.low + tb.deltaOpen)
                    close = self.getPriceFromRelative(digits, tb.low + tb.deltaClose)
                    trendbars.append({
                        "timestamp": tb.utcTimestamp,
                        "low": low,
                        "high": high,
                        "open": open_,
                        "close": close,
                        "volume": getattr(tb, "volume", 0),
                    })

                d.callback(trendbars)

            req = ProtoOAGetTrendbarsReq()
            req.ctidTraderAccountId = self.account_id
            req.symbolId = int(symbol_id)
            req.period = ProtoOATrendbarPeriod.Value(period_map[interval])
            req.fromTimestamp = start_time
            req.toTimestamp = end_time

            self.client.send(req).addCallback(on_trendbars_response).addErrback(d.errback)
            return d

        try:
            result = threads.blockingCallFromThread(reactor, run)
            return result
        except Exception as e:
            raise Exception(f"Failed to fetch historical candles for '{symbol}': {e}")
 
    def get_trading_pairs(self):
        def run():
            d = defer.Deferred()

            def on_symbols_list(response):
                response = parse_payload(response)

                symbols_data = []
                if hasattr(response, "symbol") and len(response.symbol) > 0:
                    for symbol in response.symbol:
                        symbol_info = {
                            "symbol_id": symbol.symbolId,
                            "symbol_name": symbol.symbolName,
                            "description": symbol.description,
                            # "base_asset_id": symbol.baseAssetId,
                            # "quote_asset_id": symbol.quoteAssetId,
                            # "enabled": symbol.enabled,
                        }
                        symbols_data.append(symbol_info)
                    d.callback(symbols_data)
                else:
                    d.errback(Exception("No symbols found."))

            symbols_req = ProtoOASymbolsListReq()
            symbols_req.ctidTraderAccountId = self.account_id
            self.client.send(symbols_req).addCallback(on_symbols_list).addErrback(d.errback)
            return d

        symbols = threads.blockingCallFromThread(reactor, run)
        return symbols
    
    def get_symbol_info(self, symbol):
        """
        Fetches detailed symbol information from cTrader API.
        Returns a dictionary containing details like tick size, min lot size, max lot size, precision, description, etc.
        """
        symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)

        print(symbol_id)

        def run():
            d = defer.Deferred()

            def on_symbol_info(response):
                response = parse_payload(response)
                if hasattr(response, "symbol"):
                    info = None
                    for sym in response.symbol:
                        info = MessageToDict(sym, preserving_proto_field_name=True)
                    d.callback(info)
                else:
                    d.errback(Exception(f"Symbol '{symbol_name}' not found in cTrader symbols list."))

            req = ProtoOASymbolByIdReq()
            req.ctidTraderAccountId = self.account_id
            req.symbolId.append(int(symbol_id))
            self.client.send(req).addCallback(on_symbol_info).addErrback(d.errback)
            return d

        try:
            result = threads.blockingCallFromThread(reactor, run)
            return result
        except Exception as e:
            raise Exception(f"Failed to get symbol info for '{symbol}': {e}")
        
    
    def get_symbol_id_by_name(self, symbol_name):
        """
        Returns the symbol ID for the given symbol name (case-insensitive).
        Raises Exception if symbol is not found.
        """
        for sym in self.symbols:
            name, sym_id = str(sym).split('|')
            if name.lower() == symbol_name.lower():
                return int(sym_id), name
            
        def run():
            d = defer.Deferred()

            def on_symbols_list(response):
                response = parse_payload(response)
                matched_symbol_id = None
                if hasattr(response, "symbol") and len(response.symbol) > 0:
                    for sym in response.symbol:
                        # Case-insensitive comparison
                        if sym.symbolName.lower() == symbol_name.lower():
                            matched_symbol_id = sym.symbolId
                            break
                if matched_symbol_id is not None:
                    d.callback(matched_symbol_id)
                else:
                    d.errback(Exception(f"Symbol '{symbol_name}' not found in symbols list."))

            symbols_req = ProtoOASymbolsListReq()
            symbols_req.ctidTraderAccountId = self.account_id
            self.client.send(symbols_req).addCallback(on_symbols_list).addErrback(d.errback)
            return d

        try:
            symbol_id = threads.blockingCallFromThread(reactor, run)
            self.symbols.add(f'{symbol_name}|{str(symbol_id)}')
            return symbol_id, symbol_name
        except Exception as e:
            raise Exception(f"Failed to get symbol ID for '{symbol_name}': {e}")

    

    def getPriceFromRelative(self, symbol_digits, relative):
        """Convert relative integer price to float based on symbol digits."""
        return round(relative / (10 ** symbol_digits), symbol_digits)

    def market_and_account_data(self, symbol, intervals, limit = 500):
        return super().market_and_account_data(symbol, intervals, limit)