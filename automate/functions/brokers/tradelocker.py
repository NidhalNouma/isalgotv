import requests
import time
from datetime import datetime
from django.utils import timezone

from automate.functions.brokers.broker import BrokerClient

class TradeLockerClient(BrokerClient):
    
    def __init__(self, account = None, username = None, password = None, server = None, type='L', current_trade=None):
        self.access_token = None
        self.account_id = None
        self.account_number = None
        self.account_currency = None
        self.account_balance = None
        self.config = None

        self.instruments_cache = {}

        if account:
            self.username = account.username
            self.password = account.password
            self.server = account.server
            self.enviroment_url = "https://live.tradelocker.com" if account.type == 'L' else "https://demo.tradelocker.com"
        else:
            self.username = username
            self.password = password
            self.server = server
            self.enviroment_url = "https://live.tradelocker.com" if type == 'L' else "https://demo.tradelocker.com"

        self.current_trade = current_trade
        self._login()

    def _login(self):
        try:
            request = requests.post(f"{self.enviroment_url}/backend-api/auth/jwt/token", json={
                "email": self.username,
                "password": self.password,
                "server": self.server
            })
            request.raise_for_status()
            data = request.json()
            self.access_token = data.get("accessToken")

            if not self.access_token:
                return {"error": "Login failed."}

            self._get_account()
            if self.account_id:
                return {"message": "Login successful."}
            else:
                return {"error": "Login failed."}
        except Exception as e:
            print("Error:", e)
            response = e.response.json() if hasattr(e, 'response') else {}
            raise Exception("Login failed: " + str(response.get('message') if response else str(e)))

    def _get_config(self):
        try:
            if self.config:
                return self.config
            data = self._send_request("GET", "/backend-api/trade/config")
            config = data.get('d', {})
            self.config = config
            return config
        except Exception as e:
            return {"error": str(e)}
    
    def _get_account(self):
        try:
            data = self._send_request("GET", "/backend-api/auth/jwt/all-accounts")
            account = data.get("accounts", [{}])[0]
            self.account_number = account.get("accNum")
            self.account_currency = account.get("currency")
            self.account_id = account.get("id")
            self.account_balance = account.get("accountBalance")

            return account
        except Exception as e:
            return {"error": str(e)}

    def _send_request(self, method, endpoint, data=None):
        url = f"{self.enviroment_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        if self.account_number:
            headers["accNum"] = str(self.account_number)
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, json=data)
            else:
                raise ValueError("Invalid HTTP method.")

            response.raise_for_status()  # Raise an error for HTTP errors
            return response.json()
        except requests.RequestException as e:
            print("Error:", e)
            return {"error": str(e)}

    @staticmethod
    def check_credentials(username, password, server, type):
        try:
            client = TradeLockerClient(username=username, password=password, server=server, type=type)

            if client.account_id:
                return {'message': "API credentials are valid.", "valid": True}
            else:
                return {'error': "Failed to retrieve account. Invalid credentials.", "valid": False}
        except Exception as e:
            return {'error': str(e), "valid": False}

    def open_trade(self, symbol, side, quantity, custom_id = ''):
        try:
            # Fetch the instrument ID for the given symbol
            instrument = self.get_instrument(symbol)

            instrument_id = instrument.get("tradableInstrumentId") if instrument else None
            if not instrument_id:
                return {'error': f"Symbol {symbol} not found."}
            
            route = next((r for r in instrument.get("routes", []) if r.get("type") == "TRADE"), None)

            if not route:
                return {'error': f"No trading route available for symbol {symbol}."}
            
            json = {
                "tradableInstrumentId": instrument_id,
                "routeId": route.get("id"),
                "qty": quantity,
                "side": side.lower(),
                "type": "market",
                "validity": "IOC",
            }

            data = self._send_request('POST', f"/backend-api/trade/accounts/{self.account_id}/orders", data=json)
            if data.get('s') != 'ok':
                raise Exception(data.get('errmsg', 'Failed to open trade.'))
            order_id = data.get('d', {}).get('orderId')

            end_exe = time.perf_counter()
            
            if order_id:
                order = self.get_order(order_id)
                position_id = order.get('positionId') if order else None
                if position_id:
                    trade_details = self.get_order_info(symbol, position_id)
                    # print(trade_details)

                    if trade_details is None:
                        raise Exception('Trade has been executed but Position was not found')

                    return {
                        'message': f"Trade opened with order ID {order_id}.",
                        'order_id': position_id,
                        'symbol': symbol,
                        'qty': trade_details.get('qty', quantity),
                        'price': trade_details.get('price', 0),
                        'time': trade_details.get('time', timezone.now()),
                        'fees': trade_details.get('fees', 0),
                        'closed_order_id': order_id,
                        'currency': self.account_currency if self.account_currency else '',
                        'end_exe': end_exe
                    }
            else:
                return {'error': "Failed to open trade."}
        except Exception as e:
            print("Error:", e)
            return {'error': str(e)}

        
    def close_trade(self, symbol, side, quantity, custom_id = ''):
        try:
            if(float(quantity) < 0.01):
                raise ValueError("Quantity must be greater than 0.01.")
            
            trade = self.current_trade

            json = {
                "qty": float(quantity),
            }

            path = f"/backend-api/trade/positions/{trade.order_id}"
            data = self._send_request('DELETE', path, data=json)

            if data.get('s') != 'ok':
                raise Exception(data.get('errmsg', 'Failed to close trade.'))

            end_exe = time.perf_counter()
            trade_details = self.get_final_trade_details(trade)

            if trade_details:
                return {
                        'message': f"Trade partially closed for order ID {trade.order_id}.", 
                        "id": trade.order_id,
                        'qty': quantity,
                        "trade_details": trade_details,
                        "end_exe": end_exe
                    }
            else:
                return {
                        'message': f"Trade closed for order ID {trade.order_id}.", 
                        "id": trade.order_id,
                        'qty': trade.volume,
                        "end_exe": end_exe
                    }
        
        except Exception as e:
            print("An error occurred:", str(e))
            return {'error': str(e)}
        

    def get_order(self, order_id):
        try:
            data = self._send_request("GET", f"/backend-api/trade/accounts/{self.account_id}/ordersHistory")
            d = data.get('d', {})
            orders = d.get('ordersHistory', [])
            if not orders or len(orders) == 0:
                return None

            config = self._get_config()
            columns = config.get('ordersConfig', {}).get('columns', [])
            # Extract the column names
            keys = [col['id'] for col in columns]

            # Combine keys with each row of values
            structured = [dict(zip(keys, row)) for row in d.get('ordersHistory', [])]

            for order in structured:
                if str(order.get("id")) == str(order_id):
                    return order
            return None
            
        except Exception as e:
            raise e

    def get_closed_orders_by_position_id(self, position_id, entry_time):
        try:
            dt = entry_time

            # Make sure it's in UTC
            if timezone.is_naive(dt):
                # if your `USE_TZ=True` you’ll usually get an aware datetime from Django,
                # but if not:
                dt = timezone.make_aware(dt, timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)

            ts_ms = int(dt.timestamp() * 1000)
            params = {
                'from': ts_ms,
            }
            data = self._send_request("GET", f"/backend-api/trade/accounts/{self.account_id}/ordersHistory", data=params)
            d = data.get('d', {})
            orders = d.get('ordersHistory', [])
            if not orders or len(orders) == 0:
                return None

            config = self._get_config()
            columns = config.get('ordersConfig', {}).get('columns', [])
            # Extract the column names
            keys = [col['id'] for col in columns]

            # Combine keys with each row of values
            structured = [dict(zip(keys, row)) for row in d.get('ordersHistory', [])]

            orders = [order for order in structured if str(order.get("positionId")) == str(position_id)]
            orders.sort(key=lambda r: r.get('lastModified', 0), reverse=True)
            return orders
        except Exception as e:
            return None


    def get_order_info(self, symbol, position_id):
        try:
            positions = self.get_open_trades()
            trade_info = [pos for pos in positions if str(pos.get("id")) == str(position_id)]

            if len(trade_info) > 0:
                row = trade_info[0]

                raw_ts = float(row.get('openDate'))
                # Assume timestamp is in milliseconds
                dt_naive = datetime.fromtimestamp(raw_ts / 1000.0)
                time_dt = timezone.make_aware(dt_naive, timezone.utc)
                # Extract relevant trade details (assuming these columns exist in the DataFrame)
                trade_details = {
                    'trade_id': row.get('id'),
                    'qty': str(row.get('qty')),
                    'price': str(row.get('avgPrice')),
                    'side': row.get('side'),
                    'time': time_dt,
                    'fees': str(abs(row.get('fee', 0))),
                }
                return trade_details
            else:
                return None
        except Exception as e:
            print("An error occurred:", str(e))
            return None
        
    
    def get_open_trades(self):
        try: 
            data = self._send_request("GET", f"/backend-api/trade/accounts/{self.account_id}/positions")
            d = data.get('d', {})

            config = self._get_config()
            columns = config.get('positionsConfig', {}).get('columns', [])
            # Extract the column names
            keys = [col['id'] for col in columns]
            # Combine keys with each row of values
            positions = [dict(zip(keys, row)) for row in d.get('positions', [])]
            return positions
        except Exception as e:
            return None

            
    def get_closed_trades(self, position_id = None, entry_time = None, lastTradeId = None):
        try:
            ts_ms = 0
            if entry_time:
                dt = entry_time

                # Make sure it's in UTC
                if timezone.is_naive(dt):
                    # if your `USE_TZ=True` you’ll usually get an aware datetime from Django,
                    # but if not:
                    dt = timezone.make_aware(dt, timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)

                ts_ms = int(dt.timestamp() * 1000)

            params = {
                # 'from': ts_ms,
            }
            # if lastTradeId:
            #     params['lastTradeId'] = lastTradeId

            data = self._send_request('GET', "/backend-api/trade/reports/close-trades-history", data=params)


            data = data.get('data', [])
            if not position_id:
                return data
            else:

                matches = [rec for rec in data if str(rec.get("positionId")) == position_id]
                matches.sort(key=lambda r: r.get('closeMilliseconds', 0), reverse=True)
                return matches
        except Exception as e:
            return None

    def get_final_trade_details(self, trade):

        closed_positions = self.get_closed_trades(trade.order_id, trade.entry_time, trade.closed_order_id)

        last_position = closed_positions[0] if closed_positions else None

        if last_position:
            # print(last_position)

            trade_list = []

            for trade_data in reversed(closed_positions):
                raw_ts = trade_data.get('closeMilliseconds', 0)
                # Assume timestamp is in milliseconds
                dt_naive = datetime.fromtimestamp(int(raw_ts) / 1000.0)
                time_dt = timezone.make_aware(dt_naive, timezone.utc)

                res = {
                    'volume': str(trade_data.get('closeAmount', '')),
                    'side': str(trade.side),

                    'open_price': str(trade.entry_price),
                    'close_price': str(trade_data.get('closePrice')),

                    'open_time': str(trade.entry_time),
                    'close_time': str(time_dt), 

                    'fees': str(abs(float(trade_data.get('commission') or 0)) + abs(float(trade_data.get('swap') or 0))), 
                    'profit': str(trade_data.get('profit')),

                    'commission': str(trade_data.get('commission')),
                    'swap': str(trade_data.get('swap')),

                }

                trade_list.append(res)

            return trade_list

        order_history = self.get_closed_orders_by_position_id(trade.order_id, trade.entry_time)

        last_trade = order_history[0] if order_history else None

        if last_trade:
            # print(last_trade)

            raw_ts = last_trade['lastModified']
            # Assume timestamp is in milliseconds
            dt_naive = datetime.fromtimestamp(int(raw_ts) / 1000.0)
            time_dt = timezone.make_aware(dt_naive, timezone.utc)
            
            res = {
                'volume': str(last_trade.get('qty')),
                'side': str(trade.side),

                'open_price': str(trade.entry_price),
                'close_price': str(last_trade.get('price')),

                'open_time': str(trade.entry_time),
                'close_time': str(time_dt),

                'fees': str(abs(float(last_trade.get('fee', 0)))),
                'profit': str(last_trade.get('profit', 0)),

                'lastModified': str(last_trade.get('lastModified'))

            }

            return res

        return None

    def get_account_balance(self, symbol: str = None):
        try:
            account = self._get_account()
            return {
                'balance': str(account.get('accountBalance', '0')),
                'currency': account.get('currency', ''),
                'id': str(account.get('id', '')),
                'name': str(account.get('name', '')),
                'status': str(account.get('status', '')),
            }
        except Exception as e:
            return {'error': str(e)}
        
    
    def get_instrument(self, symbol):
        try:
            if symbol in self.instruments_cache:
                return self.instruments_cache[symbol]

            data = self._send_request("GET", f"/backend-api/trade/accounts/{self.account_id}/instruments")
            instruments = data.get('d', {}).get("instruments", [])
            for instrument in instruments:  
                if instrument.get("name") == symbol:
                    self.instruments_cache[symbol] = instrument
                    return instrument
            raise ValueError(f"Instrument with symbol {symbol} not found.")
        except Exception as e:
            raise e
        
    def get_trading_pairs(self):
        try:
            data = self._send_request("GET", f"/backend-api/trade/accounts/{self.account_id}/instruments")
            instruments = data.get('d', {}).get("instruments", [])
            return [inst.get("name") for inst in instruments]
        except Exception as e:
            return {'error': str(e)}
        
    def get_history_candles(self, symbol, interval, limit=100):
        try:
            instrument= self.get_instrument(symbol)
            if not instrument:
                return {'error': f"Symbol {symbol} not found."}

            interval_map = {
                '1m': ('1m', 60),
                '5m': ('5m', 300),
                '15m': ('15m', 900),
                '30m': ('30m', 1800),
                '1h': ('1H', 3600),
                '4h': ('4H', 14400),
                '1d': ('1D', 86400),
                '1w': ('1W', 604800),
                '1mn': ('1M', 2592000),
            }

            tl_interval = interval_map.get(interval)
            if not tl_interval:
                return {'error': f"Interval {interval} is not supported."}

            end_ts = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
            start_ts = end_ts - (limit * tl_interval[1] * 1000)


            info_routes = [r for r in instrument.get("routes", []) if r.get("type") == "INFO"]
            for route in info_routes:
                params = {
                    "tradableInstrumentId": instrument.get("tradableInstrumentId"),
                    "routeId": int(route.get("id")),
                    "from": start_ts,
                    "to": end_ts,
                    "resolution": tl_interval[0],
                }

                data = self._send_request("GET", f"/backend-api/trade/history", data=params)
                if data.get('s') == 'ok':
                    candles_data = data.get('d', {}).get('barDetails', [])
                    if not candles_data:
                        continue

                    candle_list = []
                    for candle in candles_data:
                        candle_list.append({
                            'time': timezone.make_aware(datetime.fromtimestamp(candle['t'] / 1000.0), timezone.utc),
                            'open': str(candle['o']),
                            'high': str(candle['h']),
                            'low': str(candle['l']),
                            'close': str(candle['c']),
                            'volume': str(candle['v']),
                        })
                    return candle_list
                
            return {'error': f"Failed to get candles for any INFO route."}
        except Exception as e:
            return {'error': str(e)}
        
    
    def get_current_price(self, symbol):
        try:
            instrument = self.get_instrument(symbol)
            if not instrument:
                return {'error': f"Symbol {symbol} not found."}

            info_routes = [r for r in instrument.get("routes", []) if r.get("type") == "INFO"]
            for route in info_routes:
                params = {
                    "tradableInstrumentId": int(instrument.get("tradableInstrumentId")),
                    "routeId": int(route.get("id")),
                }
                data = self._send_request("GET", f"/backend-api/trade/quotes", data=params)
                # print(data, instrument)
                if data.get('s') == 'ok':
                    d = data.get('d', {})
                    ask = d.get('ap')
                    bid = d.get('bp')
                    return {
                        "ask": float(ask),
                        "bid": float(bid)
                    }
            # If none returned ok
            return {'error': "Failed to get current price for any INFO route."}
        except Exception as e:
            return {'error': str(e)}
        
    def get_symbol_info(self, symbol):
        try:
            instrument = self.get_instrument(symbol)
            if not instrument:
                return {'error': f"Symbol {symbol} not found."}

            info_routes = [r for r in instrument.get("routes", []) if r.get("type") == "INFO"]
            instrument_id = instrument.get("tradableInstrumentId")
            for route in info_routes:
                params = {
                    "locale": 'en',
                    "routeId": int(route.get("id")),
                }
                data = self._send_request("GET", f"/backend-api/trade/instruments/{instrument_id}", data=params)
                if data.get('s') == 'ok':
                    d = data.get('d', {})
                    return d
            
            return {'error': f"Symbol info for {symbol} not found."}
        except Exception as e:
            return {'error': str(e)}
        
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

