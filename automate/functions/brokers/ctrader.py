import requests
import uuid
import threading
import datetime, calendar
import time
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
    pass
    # print("Message received: \n( ", Protobuf.extract(message), " )")

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

    def __init__(self, account=None, authorization_code=None, type: str = 'demo', current_trade=None):

        self.type = type
        self.port = EndPoints.PROTOBUF_PORT
        self.host = EndPoints.PROTOBUF_LIVE_HOST if type.lower() == ('l', 'live') else EndPoints.PROTOBUF_DEMO_HOST
        
        self.account_id = None
        if account: 
            authorization_code = account.server
            self.account_id = int(account.username)
            self._id = account.id

        
        tokens = self.get_access_token(authorization_code)
        self.access_token = tokens.get('access_token')
        self.refresh_token = tokens.get('refresh_token')
        self.expires_at = tokens.get('expires_at')
        self.tokens = f'{self.access_token}||{self.refresh_token}||{self.expires_at}'

        is_new_token = tokens.get('is_new_token')
        if is_new_token and account:
            self.save_token()

        self.symbols = set()
        self.assets = set()

        self.current_trade = current_trade
        
        if not self.account_id:
            acc = self.get_first_account()
            self.account_id = acc.get('account_id', None)
            self.type = 'live' if acc.get('is_live', False) else 'demo'

        self.authorize_account()
        print('✅ Account ID set to', self.account_id)

    @property
    def client(self):
        return d_client

    def save_token(self):
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
            expires_at = codes[2] if len(codes) > 2 else None

            if expires_at:
                expire_time = datetime.datetime.fromisoformat(expires_at)
                now = datetime.datetime.now(datetime.timezone.utc)

                # Compute remaining time
                remaining = expire_time - now
                print(f'Token still valid for {remaining}')

                # Check if more than one day (24 hours)
                if remaining.total_seconds() > (24 * 60 * 60):
                    return {
                        'access_token': code,
                        'expires_at': expires_at,
                        'refresh_token': refresh_token,
                        'is_new_token': False
                    }
                            

            print('Getting new token ...')
            
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
                expires_in = int(res_json.get('expiresIn'))
                expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)).isoformat()
  
                return {
                    'access_token': res_json.get('accessToken'),
                    'expires_in': expires_in,
                    'expires_at': expires_at,
                    'refresh_token': res_json.get('refresh_token'),
                    'is_new_token': True
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

    def get_account_info(self):
        def run():
            d = defer.Deferred()
            print(f"Requesting balance for account ID: {self.account_id}")
            info_req = ProtoOATraderReq()
            info_req.ctidTraderAccountId = self.account_id

            def on_info(info):
                info = parse_payload(info)
                # print("📊 Trader info:", info)
                d.callback(info.trader)

            self.client.send(info_req).addCallback(on_info).addErrback(d.errback)
            return d

        balance = threads.blockingCallFromThread(reactor, run)
        return balance

    def get_account_balance(self):
        account = self.get_account_info()

        if hasattr(account, "balance"):
            return account.balance
        else:
            raise Exception("depositAssetId not found in trader info")
    
    def get_account_currency(self):
        try:
            account = self.get_account_info()
            deposit_asset_id = account.depositAssetId
            return self.get_asset_by_id(deposit_asset_id)
        except Exception as e:
            raise Exception(f"Failed to get account currency: {e}")
    
    def open_trade(self, symbol, action_type: str, lot_size, custom_id=''):
        """
        Opens a new trade (market order) using ProtoOASendOrderReq.
        Returns the order details or an error message.
        """

        try:
            # Get symbol ID
            symbol_info= self.get_symbol_info(symbol)
            symbol_id = symbol_info.get('symbolId')
            symbol_lot_size = symbol_info.get('lotSize')

            # Determine BUY or SELL
            side = ProtoOATradeSide.BUY if action_type.lower() in ["buy", "long"] else ProtoOATradeSide.SELL

            volume = int(float(lot_size) * float(symbol_lot_size))

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
            end_exe = time.perf_counter()
            print(f"✅ Trade opened successfully: {result}")
            order_id = result.get('orderId')

            orderInfo = self.get_order_info(symbol, order_id)
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': orderInfo.get('position_id'),
                'symbol': symbol,
                'price': orderInfo.get('price'),
                'time': orderInfo.get('time'),
                'qty': volume,
                'currency': self.get_account_currency(),
                'end_exe': end_exe,
            }

        except Exception as e:
            print("❌ Error opening trade:", e)
            return {"error": str(e)}

    def close_trade(self, symbol, side, partial_close=0):
        try:
            trade = self.current_trade
            position_id_toclose = trade.order_id

            close_volume = int(float(partial_close))

            def run():
                d = defer.Deferred()

                def on_close_response(close_res):
                    close_res = parse_payload(close_res)
                    if hasattr(close_res, "position"):
                        position_info = MessageToDict(close_res.position, preserving_proto_field_name=True)
                        d.callback(position_info)
                    else:
                        d.errback(Exception("Failed to close position or invalid response."))

                req = ProtoOAClosePositionReq()
                req.ctidTraderAccountId = self.account_id
                req.positionId = int(position_id_toclose)
                req.volume = close_volume

                self.client.send(req).addCallback(on_close_response).addErrback(d.errback)
                return d

            result = threads.blockingCallFromThread(reactor, run)
            end_exe = time.perf_counter()
            print(f"✅ Trade closed successfully: {result}")

            time.sleep(1)
            closed_positions = self.get_closed_position_by_id(result.get("positionId"), self.convert_time_to_timestamp(trade.entry_time))

            return {
                'message': f"Trade closed for position ID {position_id_toclose}.", 
                "symbol": symbol,
                'qty': close_volume,
                'order_id': self.current_trade.order_id,
                "closed_order_id": result.get('orderId', ''),
                "trade_details": closed_positions,
                'end_exe': end_exe,
            }

        except Exception as e:
            print("❌ Error closing trade:", e)
            return {"error": str(e)}

    def get_positions(self):
        """
        Retrieves all open positions for the account.
        """
        def run():
            d = defer.Deferred()

            def on_response(response):
                res = parse_payload(response)

                if hasattr(res, "position"):
                    positions = [p for p in res.position]
                    d.callback(positions)
                else:
                    d.callback([])
            
            req = ProtoOAReconcileReq()
            req.ctidTraderAccountId = self.account_id
            self.client.send(req).addCallback(on_response).addErrback(d.errback)
            return d

        try:
            positions = threads.blockingCallFromThread(reactor, run)
            return positions
        except Exception as e:
            raise Exception(f"Failed to get positions: {e}")
        
    def get_closed_position_by_id(self, position_id, fromTimestamp:int = None):
        """
        Retrieve details of a closed position using its position ID from the deal history.
        """
        def run():
            d = defer.Deferred()
            def on_deal_list(response):
                res = parse_payload(response)
                if hasattr(res, "deal"):
                    matched_deals = []
                    for deal in res.deal:
                        if getattr(deal, "positionId", None) == int(position_id):
                            deal_info = MessageToDict(deal, preserving_proto_field_name=True)
                            matched_deals.append(deal_info)
                    if matched_deals:
                        d.callback(matched_deals)
                        return
                d.errback(Exception(f"No deals found for position ID {position_id}."))
            
            req = ProtoOADealListReq()
            req.ctidTraderAccountId = self.account_id

            # Define a time window (e.g., last 30 days)
            now = datetime.datetime.now(datetime.timezone.utc)

            if not fromTimestamp:
                from_time = int(calendar.timegm((now - datetime.timedelta(days=30)).utctimetuple()) * 1000)
                to_time = int(calendar.timegm(now.utctimetuple()) * 1000)
            else:
                from_time = int(fromTimestamp)
                to_time = int(calendar.timegm(now.utctimetuple()) * 1000)

            req.fromTimestamp = from_time
            req.toTimestamp = to_time
            # Optionally limit or filter by fromTimestamp if you want recent only
            self.client.send(req).addCallback(on_deal_list).addErrback(d.errback)
            return d

        try:
            deal_info = threads.blockingCallFromThread(reactor, run)
            simplified = []

            for deal in deal_info:
                try:
                    close_detail = deal.get("closePositionDetail", {})
                    if not close_detail:
                        continue
                    money_digits = int(close_detail.get("moneyDigits", 2))

                    # Convert values using moneyDigits for precision
                    profit_raw = float(close_detail.get("grossProfit", 0))
                    swap_raw = float(close_detail.get("swap", 0))
                    commission_raw = float(close_detail.get("commission", 0))

                    # Apply scaling for actual monetary values
                    profit = profit_raw / (10 ** money_digits)
                    fee = abs((commission_raw + swap_raw) / (10 ** money_digits))

                    price = float(deal.get("executionPrice", 0))
                    time = self.convert_timestamp(deal.get("executionTimestamp"))
                    volume = float(deal.get("volume", 0))
                    symbolId = str(deal.get("symbolId", ""))
                    side = str(deal.get("tradeSide", ""))

                    simplified.append({
                        "orderId": deal.get("orderId"),
                        "dealId": deal.get("dealId"),
                        "symbolId": symbolId,
                        "side": side,
                        "close_time": str(time),
                        "close_price": price,
                        "volume": volume,
                        "fees": fee,
                        "profit": profit,
                    })
                except Exception as e:
                    print(f"⚠️ Error simplifying deal {deal.get('dealId')}: {e}")
                    continue

            return list(reversed(simplified))
        except Exception as e:
            raise Exception(f"Failed to get closed position {position_id}: {e}")
        
    def get_order_info(self, symbol, order_id):
        """
        Fetch detailed information about a specific order from cTrader API.
        Returns details like open price, open time, lot size, id, stop loss, take profit, etc.
        """
        try:
            symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)

            def run():
                d = defer.Deferred()

                def on_order_info(response):
                    res = parse_payload(response)
                    if hasattr(res, "order"):
                        order = res.order
                        order_data = MessageToDict(order, preserving_proto_field_name=True)

                        trade_data = order_data.get('tradeData')

                        # Extract and format key details
                        info = {
                            "trade_id": order_data.get("orderId"),
                            "symbol_id": symbol_id,
                            "symbol": symbol_name,
                            "side": trade_data.get("tradeSide"),
                            "qty": order_data.get("executedVolume", None),
                            "price": order_data.get('executionPrice'),
                            "time": self.convert_timestamp(trade_data.get("openTimestamp", None)),
                            "position_id": order_data.get("positionId", None),
                            "fees": 0
                        }
                        d.callback(info)
                    else:
                        d.errback(Exception(f"Order with ID {order_id} not found."))

                req = ProtoOAOrderDetailsReq()
                req.ctidTraderAccountId = self.account_id
                req.orderId = int(order_id)
                self.client.send(req).addCallback(on_order_info).addErrback(d.errback)
                return d

            result = threads.blockingCallFromThread(reactor, run)
            print(f"📋 Order Info Retrieved: {result}")
            return result

        except Exception as e:
            print("❌ Error fetching order info:", e)
            return {"error": str(e)}
        
        
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
        symbol_info = self.get_symbol_info(symbol=symbol)
        symbol_id = symbol_info.get('symbolId')
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
        now = datetime.datetime.now(datetime.timezone.utc)
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
                # print(res)

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
                        "timestamp": self.convert_timestamp(tb.utcTimestampInMinutes * 60 * 1000),
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

    def get_asset_by_id(self, asset_id: int):
        """
        Fetch the asset name (e.g., USD, EUR) for a given asset_id using ProtoOAAssetListReq.
        """

        for ass in self.assets:
            name, ass_id = str(ass).split('|')
            if asset_id == int(ass_id):
                return name
            
        def run():
            d = defer.Deferred()

            def on_asset_list(response):
                response = parse_payload(response)
                if hasattr(response, "asset"):
                    for asset in response.asset:
                        if str(asset.assetId) == str(asset_id):
                            d.callback(asset.name)
                            return
                d.errback(Exception(f"Asset with ID {asset_id} not found."))

            req = ProtoOAAssetListReq()
            req.ctidTraderAccountId = self.account_id
            self.client.send(req).addCallback(on_asset_list).addErrback(d.errback)
            return d

        try:
            asset_name = threads.blockingCallFromThread(reactor, run)
            self.assets.add(f'{asset_name}|{str(asset_id)}')
            return asset_name
        except Exception as e:
            raise Exception(f"Failed to get asset name for ID {asset_id}: {e}")

    

    def getPriceFromRelative(self, symbol_digits, relative):
        """Convert relative integer price to float based on symbol digits."""
        return round(relative / (10 ** symbol_digits), symbol_digits)
  
    def market_and_account_data(self, symbol: str, intervals: list, limit: int = 500) -> dict:
        try:
            symbol_info = self.get_symbol_info(symbol)
            history_candles = {} 
            for interval in intervals:
                if interval not in ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1mn']:
                    return {'error': f"Interval {interval} is not supported. use one of ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1mn']"}
                
                candles = self.get_history_candles(symbol, interval, limit)
                history_candles[interval] = candles
            account_balance = self.get_account_balance()
            current_price = self.get_current_price(symbol)

            return {
                "history_candles": history_candles,
                "account_info": account_balance,
                "current_price": current_price,
                "symbol_info": symbol_info
            }
        except Exception as e:
            return {'error': str(e)}