# Size will be in lot size and it will be converted to unit size based on the contract size of the symbol.
# Currently only supports demo accounts.

import requests
import uuid
import threading
import datetime
import calendar
import time
from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from google.protobuf.json_format import MessageToDict

from twisted.internet import reactor, defer, threads
from twisted.internet.defer import Deferred

from django.conf import settings
from django.urls import reverse

from automate.models import ForexBrokerAccount
from automate.functions.brokers.broker import BrokerClient

import environ

env = environ.Env()

CLIENT_ID = env('CTRADER_CLIENT_ID')
CLIENT_SECRET = env('CTRADER_SECRET_KEY')


class CtraderConnectionManager:
    """
    Manages persistent connection to cTrader demo server.
    Uses connection pooling to avoid re-establishing connections for each request.
    Singleton pattern ensures only one instance manages all connections.
    
    NOTE: Currently only demo accounts are supported.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._client = None
        self._connected = threading.Event()
        self._authenticated = False
        self._reactor_started = threading.Event()
        self._lock = threading.Lock()

        # Account authorization cache: {account_id: timestamp}
        self._authorized_accounts = {}
        self._auth_cache_ttl = 300  # 5 minutes

        # Symbol/asset caches per account
        self._symbol_cache = {}
        self._asset_cache = {}
        self._symbol_info_cache = {}

        self._start_reactor()
        
        # Eagerly start the connection so it's ready when first request comes
        self._start_connection_async()

    def _start_reactor(self):
        """Start the Twisted reactor in a background thread."""
        # If reactor is already running, just mark as started
        if reactor.running:
            self._reactor_started.set()
            print(" Twisted reactor already running")
            return
            
        def run_reactor():
            # Schedule a callback to set the event once reactor is actually running
            reactor.callWhenRunning(lambda: (self._reactor_started.set(), print(" Twisted reactor started")))
            reactor.run(installSignalHandlers=False)

        thread = threading.Thread(target=run_reactor, daemon=True)
        thread.start()
        
        # Wait for reactor to be fully running before continuing
        if not self._reactor_started.wait(timeout=10):
            print("Warning: Twisted reactor may not have started properly")
        else:
            print(" Twisted reactor ready")

    def _start_connection_async(self):
        """Start the cTrader connection asynchronously (don't wait for it)."""
        def start():
            if self._client is None:
                self._connected.clear()
                self._authenticated = False
                self._client = self._create_client()
                self._client.startService()
                print(" cTrader connection started (async)")
        
        # Schedule connection start on reactor thread
        reactor.callFromThread(start)

    def _create_client(self):
        """Create and configure a new cTrader demo client."""
        client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)

        def on_connected(c):
            print(f"\n cTrader Demo Connected to {EndPoints.PROTOBUF_DEMO_HOST}")
            request = ProtoOAApplicationAuthReq()
            request.clientId = CLIENT_ID
            request.clientSecret = CLIENT_SECRET
            
            deferred = c.send(request, responseTimeoutInSeconds=30)

            def on_auth_success(result):
                self._authenticated = True
                self._connected.set()
                print(f" cTrader Demo Application Authenticated Successfully")

            def on_auth_error(failure):
                error_details = str(failure)
                print(f" cTrader Demo Auth Error: {error_details}")
                self._connected.set()

            deferred.addCallback(on_auth_success)
            deferred.addErrback(on_auth_error)

        def on_disconnected(c, reason):
            print(f"\n cTrader Demo Disconnected: {reason}")
            self._connected.clear()
            self._authenticated = False
            self._client = None

        def on_message(c, message):
            pass

        client.setConnectedCallback(on_connected)
        client.setDisconnectedCallback(on_disconnected)
        client.setMessageReceivedCallback(on_message)

        return client

    def get_client(self, timeout=60):
        """Get a connected and authenticated demo client."""
        # Return existing client if already connected and authenticated
        if self._client is not None and self._authenticated:
            return self._client
        
        # Ensure reactor is running
        if not self._reactor_started.is_set():
            if not self._reactor_started.wait(timeout=10):
                raise Exception("Twisted reactor failed to start. Please restart the application.")
        
        # If client doesn't exist yet, start it (in case _start_connection_async hasn't run yet)
        with self._lock:
            if self._client is None:
                self._connected.clear()
                self._authenticated = False
                self._client = self._create_client()
                print(" Starting cTrader client service...")
                reactor.callFromThread(self._client.startService)
        
        # Wait for connection - the connection may have started at init time
        # so just wait for it to complete
        print(f" Waiting for cTrader connection (timeout={timeout}s)...")
        
        if self._connected.wait(timeout=timeout):
            if self._authenticated:
                print(" cTrader client ready")
                return self._client
            else:
                # Connected but auth failed
                self._client = None
                raise Exception("cTrader Demo authentication failed. Please try again.")
        
        # Timeout
        print(" cTrader connection timeout")
        self._client = None
        raise Exception("Timeout connecting to cTrader Demo server. Please try again.")
        
        return self._client

    def is_account_authorized(self, account_id):
        if account_id in self._authorized_accounts:
            auth_time = self._authorized_accounts[account_id]
            if time.time() - auth_time < self._auth_cache_ttl:
                return True
        return False

    def mark_account_authorized(self, account_id):
        self._authorized_accounts[account_id] = time.time()

    def invalidate_account_auth(self, account_id):
        self._authorized_accounts.pop(account_id, None)

    def get_cached_symbol_id(self, account_id, symbol_name):
        account_cache = self._symbol_cache.get(account_id, {})
        return account_cache.get(symbol_name.lower())

    def cache_symbol_id(self, account_id, symbol_name, symbol_id):
        if account_id not in self._symbol_cache:
            self._symbol_cache[account_id] = {}
        self._symbol_cache[account_id][symbol_name.lower()] = symbol_id

    def get_cached_asset(self, account_id, asset_id):
        account_cache = self._asset_cache.get(account_id, {})
        return account_cache.get(asset_id)

    def cache_asset(self, account_id, asset_id, asset_name):
        if account_id not in self._asset_cache:
            self._asset_cache[account_id] = {}
        self._asset_cache[account_id][asset_id] = asset_name

    def get_cached_symbol_info(self, account_id, symbol_id):
        account_cache = self._symbol_info_cache.get(account_id, {})
        return account_cache.get(symbol_id)

    def cache_symbol_info(self, account_id, symbol_id, info):
        if account_id not in self._symbol_info_cache:
            self._symbol_info_cache[account_id] = {}
        self._symbol_info_cache[account_id][symbol_id] = info


_connection_manager = None
_manager_lock = threading.Lock()


def get_connection_manager():
    global _connection_manager
    if _connection_manager is None:
        with _manager_lock:
            if _connection_manager is None:
                _connection_manager = CtraderConnectionManager()
    return _connection_manager


def parse_payload(payload):
    if hasattr(payload, "payload"):
        try:
            parsed = Protobuf.extract(payload)
            payload = parsed
        except Exception as e:
            print("Failed to decode payload:", e)
    return payload


class CtraderClient(BrokerClient):

    def __init__(self, account=None, authorization_code=None, type: str = 'demo', current_trade=None, skip_auth=False):
        self.type = type.lower()
        self.is_demo = self.type in ('demo', 'd')

        self.account_id = None
        self._id = None

        if account:
            authorization_code = account.server
            self.account_id = int(account.username)
            self._id = account.id
            if hasattr(account, 'account_type'):
                self.is_demo = account.account_type.lower() in ('demo', 'd')

        tokens = self.get_access_token(authorization_code)
        self.access_token = tokens.get('access_token')
        self.refresh_token = tokens.get('refresh_token')
        self.expires_at = tokens.get('expires_at')
        self.tokens = f'{self.access_token}||{self.refresh_token}||{self.expires_at}'

        is_new_token = tokens.get('is_new_token')
        if is_new_token and account:
            self.save_token()

        self.current_trade = current_trade
        self._conn_manager = get_connection_manager()

        if not self.account_id:
            acc = self.get_first_account()
            if not acc:
                raise Exception("No trading account found.")
            self.account_id = acc.get('account_id', None)
            self.is_demo = not acc.get('is_live', False)
            self.type = 'D' if self.is_demo else 'L'

        # Check if this is a live account - not supported yet
        if not self.is_demo:
            raise Exception("cTrader live accounts are not supported yet. Please use a demo account.")

        if not skip_auth:
            self.authorize_account()
            print(f'Account ID set to {self.account_id} ({self.type})')

    @property
    def client(self):
        return self._conn_manager.get_client()

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
            # Create a temporary client to get account info and validate
            temp_client = CtraderClient(authorization_code=authorization_code, type=type, skip_auth=True)
            
            # Check if this is a live account - not supported yet
            if not temp_client.is_demo:
                raise Exception("cTrader live accounts are not supported yet. Please use a demo account.")
            
            # Authorize the account
            temp_client.authorize_account()
            print(f'Account ID set to {temp_client.account_id} ({temp_client.type})')
            
            return {
                "error": None,
                "valid": True,
                "ctrader_access_token": temp_client.tokens,
                "account_id": temp_client.account_id,
                "account_type": temp_client.type,
            }
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
                remaining = expire_time - now
                print(f'Token still valid for {remaining}')

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
                host = f"http://{settings.PARENT_HOST}" if ("local" in settings.PARENT_HOST or "127" in settings.PARENT_HOST) else f"https://www.{settings.PARENT_HOST}"
                redirect_url = f"{host}{reverse('ctrader_auth_code')}"
                data = {
                    "grant_type": "authorization_code",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_url
                }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = requests.post(url=EndPoints.TOKEN_URI, data=data, headers=headers)
            response.raise_for_status()
            res_json = response.json()

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

    def _send_request(self, request, callback, timeout=30):
        def run():
            d = defer.Deferred()

            def on_response(result):
                try:
                    parsed = parse_payload(result)
                    response_data = callback(parsed)
                    d.callback(response_data)
                except Exception as e:
                    d.errback(e)

            def on_timeout():
                if not d.called:
                    request_type = type(request).__name__
                    d.errback(Exception(f"Request timeout for {request_type}. Connection may still be establishing."))

            # Use 30 second timeout for API requests
            self.client.send(request, responseTimeoutInSeconds=30).addCallback(on_response).addErrback(d.errback)
            reactor.callLater(timeout, on_timeout)
            return d

        return threads.blockingCallFromThread(reactor, run)

    def get_first_account(self, account_id=None):
        def callback(result):
            if hasattr(result, "ctidTraderAccount") and len(result.ctidTraderAccount) > 0:
                if account_id:
                    for acc in result.ctidTraderAccount:
                        if str(acc.ctidTraderAccountId) == str(account_id):
                            return {
                                'account_id': acc.ctidTraderAccountId,
                                'is_live': acc.isLive,
                                'login': acc.traderLogin,
                            }
                account = result.ctidTraderAccount[0]
                return {
                    'account_id': account.ctidTraderAccountId,
                    'is_live': account.isLive,
                    'login': account.traderLogin,
                }
            raise Exception("No trading account found.")

        account_list_req = ProtoOAGetAccountListByAccessTokenReq()
        account_list_req.accessToken = self.access_token
        return self._send_request(account_list_req, callback)

    def authorize_account(self, max_retries=3):
        if self._conn_manager.is_account_authorized(self.account_id):
            print("Account already authorized (cached).")
            return True

        def callback(result):
            print("Account authorized successfully.")
            self._conn_manager.mark_account_authorized(self.account_id)
            return True

        auth_req = ProtoOAAccountAuthReq()
        auth_req.ctidTraderAccountId = self.account_id
        auth_req.accessToken = self.access_token

        last_error = None
        for attempt in range(max_retries):
            try:
                result = self._send_request(auth_req, callback)
                return result
            except Exception as e:
                last_error = e
                error_msg = str(e)
                if attempt < max_retries - 1:
                    if "timeout" in error_msg.lower() or "Timeout" in error_msg:
                        print(f"Authorization attempt {attempt + 1} timed out, retrying...")
                        time.sleep(2)  # Longer delay before retry
                        continue
                # If not a timeout or last attempt, re-raise
                if "timeout" not in error_msg.lower():
                    break
        
        raise Exception(f"Account authorization failed after {max_retries} attempts: {last_error}")

    def get_account_info(self):
        def callback(result):
            return result.trader

        info_req = ProtoOATraderReq()
        info_req.ctidTraderAccountId = self.account_id
        return self._send_request(info_req, callback)

    def get_account_balance(self):
        account = self.get_account_info()
        if hasattr(account, "balance"):
            return account.balance
        else:
            raise Exception("balance not found in trader info")

    def get_account_currency(self):
        try:
            account = self.get_account_info()
            deposit_asset_id = account.depositAssetId
            return self.get_asset_by_id(deposit_asset_id)
        except Exception as e:
            raise Exception(f"Failed to get account currency: {e}")

    def open_trade(self, symbol, action_type: str, lot_size, custom_id=''):
        try:
            symbol_info = self.get_symbol_info(symbol)
            symbol_id = symbol_info.get('symbolId')
            symbol_lot_size = symbol_info.get('lotSize')

            side = ProtoOATradeSide.BUY if action_type.lower() in ["buy", "long"] else ProtoOATradeSide.SELL
            volume = int(float(lot_size) * float(symbol_lot_size))
            client_order_id = custom_id if custom_id else str(uuid.uuid4())[:12]

            def callback(res):
                if hasattr(res, "order"):
                    return MessageToDict(res.order, preserving_proto_field_name=True)
                if hasattr(res, "errorCode"):
                    raise Exception(f"Order rejected: {res.errorCode}. {res.description}")
                raise Exception("Unknown response format from cTrader.")

            req = ProtoOANewOrderReq()
            req.ctidTraderAccountId = self.account_id
            req.symbolId = int(symbol_id)
            req.orderType = ProtoOAOrderType.MARKET
            req.tradeSide = side
            req.volume = volume
            req.clientOrderId = client_order_id

            result = self._send_request(req, callback)
            end_exe = time.perf_counter()
            print(f"Trade opened successfully: {result}")
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
            print("Error opening trade:", e)
            return {"error": str(e)}

    def close_trade(self, symbol, side, partial_close=0):
        try:
            trade = self.current_trade
            position_id_toclose = trade.order_id
            close_volume = int(float(partial_close))
            
            position = self.get_position_by_id(position_id_toclose)
            # print(f"Position to close: {position}")
            if not position:
                raise Exception(f"Position with ID {position_id_toclose} not found.")
            position_volume = int(position.get('tradeData', {}).get('volume', close_volume))
            if close_volume > position_volume:
                close_volume = position_volume

            def callback(close_res):
                if hasattr(close_res, "position"):
                    return MessageToDict(close_res.position, preserving_proto_field_name=True)
                if hasattr(close_res, "errorCode"):
                    raise Exception(f"Close position rejected: {close_res.errorCode}. {close_res.description}")

                raise Exception("Failed to close position.")

            req = ProtoOAClosePositionReq()
            req.ctidTraderAccountId = self.account_id
            req.positionId = int(position_id_toclose)
            req.volume = close_volume

            result = self._send_request(req, callback)
            end_exe = time.perf_counter()
            print(f"Trade closed successfully: {result}")

            time.sleep(1)
            closed_positions = self.get_closed_position_by_id(
                result.get("positionId"),
                self.convert_time_to_timestamp(trade.entry_time)
            )

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
            print("Error closing trade:", e)
            return {"error": str(e)}

    def get_positions(self):
        def callback(res):
            if hasattr(res, "position"):
                return [p for p in res.position]
            return []

        req = ProtoOAReconcileReq()
        req.ctidTraderAccountId = self.account_id

        try:
            return self._send_request(req, callback)
        except Exception as e:
            raise Exception(f"Failed to get positions: {e}")

    def get_position_by_id(self, position_id):
        positions = self.get_positions()
        for pos in positions:
            if getattr(pos, "positionId", None) == int(position_id):
                return MessageToDict(pos, preserving_proto_field_name=True)
        raise Exception(f"Position with ID {position_id} not found.")

    def get_closed_position_by_id(self, position_id, fromTimestamp: int = None):
        def callback(res):
            if hasattr(res, "deal"):
                matched_deals = []
                for deal in res.deal:
                    if getattr(deal, "positionId", None) == int(position_id):
                        deal_info = MessageToDict(deal, preserving_proto_field_name=True)
                        matched_deals.append(deal_info)
                if matched_deals:
                    return matched_deals
            raise Exception(f"No deals found for position ID {position_id}.")

        now = datetime.datetime.now(datetime.timezone.utc)

        if not fromTimestamp:
            from_time = int(calendar.timegm((now - datetime.timedelta(days=30)).utctimetuple()) * 1000)
            to_time = int(calendar.timegm(now.utctimetuple()) * 1000)
        else:
            from_time = int(fromTimestamp)
            to_time = int(calendar.timegm(now.utctimetuple()) * 1000)

        req = ProtoOADealListReq()
        req.ctidTraderAccountId = self.account_id
        req.fromTimestamp = from_time
        req.toTimestamp = to_time

        try:
            deal_info = self._send_request(req, callback)
            simplified = []

            for deal in deal_info:
                try:
                    close_detail = deal.get("closePositionDetail", {})
                    if not close_detail:
                        continue
                    money_digits = int(close_detail.get("moneyDigits", 2))

                    profit_raw = float(close_detail.get("grossProfit", 0))
                    swap_raw = float(close_detail.get("swap", 0))
                    commission_raw = float(close_detail.get("commission", 0))

                    profit = profit_raw / (10 ** money_digits)
                    fee = abs((commission_raw + swap_raw) / (10 ** money_digits))

                    price = float(deal.get("executionPrice", 0))
                    time_val = self.convert_timestamp(deal.get("executionTimestamp"))
                    volume = float(deal.get("volume", 0))
                    symbolId = str(deal.get("symbolId", ""))
                    deal_side = str(deal.get("tradeSide", ""))

                    simplified.append({
                        "orderId": deal.get("orderId"),
                        "dealId": deal.get("dealId"),
                        "symbolId": symbolId,
                        "side": deal_side,
                        "close_time": str(time_val),
                        "close_price": price,
                        "volume": volume,
                        "fees": fee,
                        "profit": profit,
                    })
                except Exception as e:
                    print(f"Error simplifying deal {deal.get('dealId')}: {e}")
                    continue

            return list(reversed(simplified))
        except Exception as e:
            raise Exception(f"Failed to get closed position {position_id}: {e}")

    def get_order_info(self, symbol, order_id):
        try:
            symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)

            def callback(res):
                if hasattr(res, "order"):
                    order = res.order
                    order_data = MessageToDict(order, preserving_proto_field_name=True)
                    trade_data = order_data.get('tradeData')

                    return {
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
                raise Exception(f"Order with ID {order_id} not found.")

            req = ProtoOAOrderDetailsReq()
            req.ctidTraderAccountId = self.account_id
            req.orderId = int(order_id)

            result = self._send_request(req, callback)
            print(f"Order Info Retrieved: {result}")
            return result
        except Exception as e:
            print("Error fetching order info:", e)
            return {"error": str(e)}

    def get_current_price(self, symbol):
        symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)

        def run():
            d = defer.Deferred()
            original_callback = [None]

            def on_spot_event(client, message):
                msg = Protobuf.extract(message)
                if msg.DESCRIPTOR.name == "ProtoOASpotEvent":
                    if getattr(msg, "symbolId", None) == symbol_id and hasattr(msg, "bid") and hasattr(msg, "ask"):
                        bid = msg.bid
                        ask = msg.ask
                        spread = ask - bid

                        unsub_req = ProtoOAUnsubscribeSpotsReq()
                        unsub_req.ctidTraderAccountId = self.account_id
                        unsub_req.symbolId.append(symbol_id)
                        self.client.send(unsub_req)

                        if original_callback[0]:
                            self.client.setMessageReceivedCallback(original_callback[0])

                        if not d.called:
                            d.callback({
                                "symbol_id": symbol_id,
                                "symbol_name": symbol_name,
                                "bid": bid,
                                "ask": ask,
                                "spread": spread
                            })

            original_callback[0] = getattr(self.client, '_messageReceivedCallback', lambda c, m: None)
            self.client.setMessageReceivedCallback(on_spot_event)

            sub_req = ProtoOASubscribeSpotsReq()
            sub_req.ctidTraderAccountId = self.account_id
            sub_req.symbolId.append(symbol_id)
            self.client.send(sub_req)

            def on_timeout():
                if not d.called:
                    if original_callback[0]:
                        self.client.setMessageReceivedCallback(original_callback[0])
                    d.errback(Exception("Timeout waiting for spot event"))

            reactor.callLater(5, on_timeout)
            return d

        try:
            result = threads.blockingCallFromThread(reactor, run)
            return result
        except Exception as e:
            raise Exception(f"Failed to get current price for '{symbol}': {e}")

    def get_history_candles(self, symbol, interval="1m", limit=500):
        symbol_info = self.get_symbol_info(symbol=symbol)
        symbol_id = symbol_info.get('symbolId')
        digits = int(symbol_info.get("digits", 5))

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

        now = datetime.datetime.now(datetime.timezone.utc)
        if "m" in interval:
            delta = datetime.timedelta(minutes=limit)
        elif "h" in interval:
            delta = datetime.timedelta(hours=limit)
        elif "d" in interval:
            delta = datetime.timedelta(days=limit)
        elif interval == "1w":
            delta = datetime.timedelta(weeks=limit)
        else:
            delta = datetime.timedelta(days=limit * 30)

        start_time = int(calendar.timegm((now - delta).utctimetuple()) * 1000)
        end_time = int(calendar.timegm(now.utctimetuple()) * 1000)

        def callback(res):
            if not hasattr(res, "trendbar") or len(res.trendbar) == 0:
                raise Exception("No trendbar data returned.")

            trendbars = []
            for tb in res.trendbar:
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
            return trendbars

        req = ProtoOAGetTrendbarsReq()
        req.ctidTraderAccountId = self.account_id
        req.symbolId = int(symbol_id)
        req.period = ProtoOATrendbarPeriod.Value(period_map[interval])
        req.fromTimestamp = start_time
        req.toTimestamp = end_time

        try:
            return self._send_request(req, callback, timeout=15)
        except Exception as e:
            raise Exception(f"Failed to fetch historical candles for '{symbol}': {e}")

    def get_trading_pairs(self):
        def callback(response):
            symbols_data = []
            if hasattr(response, "symbol") and len(response.symbol) > 0:
                for symbol in response.symbol:
                    symbol_info = {
                        "symbol_id": symbol.symbolId,
                        "symbol_name": symbol.symbolName,
                        "description": symbol.description,
                    }
                    symbols_data.append(symbol_info)
                    self._conn_manager.cache_symbol_id(
                        self.account_id, symbol.symbolName, symbol.symbolId
                    )
                return symbols_data
            raise Exception("No symbols found.")

        symbols_req = ProtoOASymbolsListReq()
        symbols_req.ctidTraderAccountId = self.account_id
        return self._send_request(symbols_req, callback, timeout=15)

    def get_symbol_info(self, symbol):
        symbol_id, symbol_name = self.get_symbol_id_by_name(symbol)

        cached_info = self._conn_manager.get_cached_symbol_info(self.account_id, symbol_id)
        if cached_info:
            return cached_info

        def callback(response):
            if hasattr(response, "symbol"):
                info = None
                for sym in response.symbol:
                    info = MessageToDict(sym, preserving_proto_field_name=True)
                if info:
                    self._conn_manager.cache_symbol_info(self.account_id, symbol_id, info)
                return info
            raise Exception(f"Symbol '{symbol_name}' not found in cTrader symbols list.")

        req = ProtoOASymbolByIdReq()
        req.ctidTraderAccountId = self.account_id
        req.symbolId.append(int(symbol_id))

        try:
            return self._send_request(req, callback)
        except Exception as e:
            raise Exception(f"Failed to get symbol info for '{symbol}': {e}")

    def get_symbol_id_by_name(self, symbol_name):
        cached_id = self._conn_manager.get_cached_symbol_id(self.account_id, symbol_name)
        if cached_id:
            return cached_id, symbol_name

        def callback(response):
            matched_symbol_id = None
            if hasattr(response, "symbol") and len(response.symbol) > 0:
                for sym in response.symbol:
                    self._conn_manager.cache_symbol_id(
                        self.account_id, sym.symbolName, sym.symbolId
                    )
                    if sym.symbolName.lower() == symbol_name.lower():
                        matched_symbol_id = sym.symbolId
            if matched_symbol_id is not None:
                return matched_symbol_id
            raise Exception(f"Symbol '{symbol_name}' not found in symbols list.")

        symbols_req = ProtoOASymbolsListReq()
        symbols_req.ctidTraderAccountId = self.account_id

        try:
            symbol_id = self._send_request(symbols_req, callback, timeout=15)
            return symbol_id, symbol_name
        except Exception as e:
            raise Exception(f"Failed to get symbol ID for '{symbol_name}': {e}")

    def get_asset_by_id(self, asset_id: int):
        cached_name = self._conn_manager.get_cached_asset(self.account_id, asset_id)
        if cached_name:
            return cached_name

        def callback(response):
            if hasattr(response, "asset"):
                for asset in response.asset:
                    self._conn_manager.cache_asset(
                        self.account_id, asset.assetId, asset.name
                    )
                    if str(asset.assetId) == str(asset_id):
                        return asset.name
            raise Exception(f"Asset with ID {asset_id} not found.")

        req = ProtoOAAssetListReq()
        req.ctidTraderAccountId = self.account_id

        try:
            return self._send_request(req, callback)
        except Exception as e:
            raise Exception(f"Failed to get asset name for ID {asset_id}: {e}")

    def getPriceFromRelative(self, symbol_digits, relative):
        return round(relative / (10 ** symbol_digits), symbol_digits)

    def convert_time_to_timestamp(self, time_str):
        if time_str is None:
            return None
        try:
            dt = datetime.datetime.fromisoformat(str(time_str).replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        except Exception:
            return None

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
    