from tradelocker import TLAPI
import requests
from datetime import datetime
from django.utils import timezone

from automate.functions.brokers.broker import BrokerClient

class TradeLockerClient(BrokerClient):
    
    def __init__(self, account = None, username = None, password = None, server = None, type='L', current_trade=None):

        if account:
            enviroment_url = "https://live.tradelocker.com" if account.type == 'L' else "https://demo.tradelocker.com"
            self.tl = TLAPI(environment=enviroment_url, username=account.username, password=account.password, server=account.server)
        else:
            enviroment_url = "https://live.tradelocker.com" if type == 'L' else "https://demo.tradelocker.com"
            self.tl = TLAPI(environment=enviroment_url, username=username, password=password, server=server)

        self.current_trade = current_trade
    
    @staticmethod
    def check_credentials(username, password, server, type):
        try:
            clinet = TradeLockerClient(username=username, password=password, server=server, type=type)
            accounts = clinet.tl.get_all_accounts()

            if len(accounts) > 0:
                return {'message': "API credentials are valid.", "valid": True}
            else:
                return {'error': "Failed to retrieve accounts.", "valid": False}
        except Exception as e:
            return {'error': str(e), "valid": False}

        
    def open_trade(self, symbol, side, quantity, custom_id = ''):
        try:
            # Fetch the instrument ID for the given symbol
            tl = self.tl
            instrument_id = tl.get_instrument_id_from_symbol_name(symbol)
            if not instrument_id:
                return {'error': f"Symbol {symbol} not found."}
            # Create a market order
            order_id = tl.create_order(instrument_id, quantity=quantity, side=side.lower(), type_="market")
            
            if order_id:
                position_id = tl.get_position_id_from_order_id(order_id)
                if position_id:
                    trade_details = self.get_order_info(symbol, position_id, order_id)
                    # print(trade_details)

                    if trade_details is None:
                        raise Exception('Trade has been executed but Position was not found')

                    account_info = tl.get_trade_accounts()
                    # print(account_info)
                    currency = account_info[0].get('currency', '')
                    return {
                        'message': f"Trade opened with order ID {order_id}.",
                        'order_id': position_id,
                        'symbol': symbol,
                        'qty': trade_details.get('qty', quantity),
                        'price': trade_details.get('price', 0),
                        'time': trade_details.get('time', timezone.now()),
                        'fees': trade_details.get('fees', 0),
                        'closed_order_id': order_id,
                        'currency': currency if currency else '',
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
            
            tl = self.tl
            result = tl.close_position(position_id = int(trade.order_id), close_quantity = float(quantity))
            trade_details = self.get_order_info(symbol, trade.order_id, trade.closed_order_id)

            if trade_details:
                return {
                        'message': f"Trade partially closed for order ID {trade.order_id}.", 
                        "id": trade.order_id,
                        'qty': quantity,
                        "closed_order_id": trade_details.get('trade_id', ''),
                    }
            else:
                return {
                        'message': f"Trade closed for order ID {trade.order_id}.", 
                        "id": trade.order_id,
                        'qty': trade.volume,
                    }
        
        except Exception as e:
            print("An error occurred:", str(e))
            return {'error': str(e)}

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
            
            orders_history = self.tl.get_all_orders(history=True, start_timestamp=ts_ms)
            # Filter orders for this position_id
            if not orders_history.empty:
                records = orders_history.to_dict(orient="records")
                # Filter for the given position_id
                matches = [rec for rec in records if str(rec.get("positionId")) == position_id]
                # Sort so the most recent (highest timestamp) comes first
                matches.sort(key=lambda r: r.get('lastModified', 0), reverse=True)
                return matches
            
            return []
        except Exception as e:
            return None


    def get_order_info(self, symbol, position_id, ladtTradeId = None):
        try:
            positions = self.tl.get_all_positions()

            if 'id' not in positions.columns:
                print("Column 'orderId' not found in orders")
                return None

            # Locate the row matching the trade ID
            trade_info = positions.loc[positions['id'] == int(position_id)]

            # Print each column name and its corresponding value for the single row
            # if not trade_info.empty:
            #     row = trade_info.iloc[0]
            #     for col in trade_info.columns:
            #         print(f"{col}: {row[col]}")
            # else:
            #     print("No trade info found")

            if not trade_info.empty:
                row = trade_info.iloc[0]
                
                raw_ts = row['openDate']
                # Assume timestamp is in milliseconds
                dt_naive = datetime.fromtimestamp(raw_ts / 1000.0)
                time_dt = timezone.make_aware(dt_naive, timezone.utc)
                # Extract relevant trade details (assuming these columns exist in the DataFrame)
                trade_details = {
                    'trade_id': row['id'],
                    'qty': str(trade_info['qty'].values[0].item()),
                    'price': str(trade_info['avgPrice'].values[0].item()),
                    'side': row['side'],
                    'time': time_dt,
                    'fees': str(abs(row.get('fee', 0))),
                }
                return trade_details
            else:
                return None
        except Exception as e:
            print("An error occurred:", str(e))
            return None

            
    def get_closed_trades(self, position_id = None, entry_time = None, lastTradeId = None):
        try:
            route_url = f"{self.tl.get_base_url()}/trade/reports/close-trades-history"
            headers = self.tl._get_headers()

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

            response = requests.get(url=route_url, params=params, headers=headers, timeout=self.tl._TIMEOUT)
            response_json = self.tl._get_response_json(response)

            data = response_json.get('data', [])

            # print(data)
            if not position_id:
                return data
            else:

                matches = [rec for rec in data if str(rec.get("positionId")) == position_id]
                matches.sort(key=lambda r: r.get('closeMilliseconds', 0), reverse=True)
                return matches
        except Exception as e:
            return None

    def get_trade_data(self, trade):

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
            dt_naive = datetime.fromtimestamp(raw_ts / 1000.0)
            time_dt = timezone.make_aware(dt_naive, timezone.utc)
            
            res = {
                'volume': str(last_trade.get('qty')),
                'side': str(trade.side),

                'open_price': str(trade.entry_price),
                'close_price': str(last_trade.get('price')),

                'open_time': str(trade.entry_time),
                'close_time': str(time_dt),

                'lastModified': str(last_trade.get('lastModified'))

            }

            return res

        return None

    def get_account_balance(self):
        try:
            account_balance = self.tl.get_all_accounts()
            if not account_balance.empty:
                row = account_balance.iloc[0]  # first row of the DataFrame
                return {
                    'balance': str(row.get('accountBalance', '0')),
                    'currency': row.get('currency', ''),
                    'id': str(row.get('id', '')),
                    'name': str(row.get('name', '')),
                    'status': str(row.get('status', '')),
                }
            else:
                return {'error': "Failed to retrieve account balance."}
        except Exception as e:
            return {'error': str(e)}
        
    def get_trading_pairs(self):
        try:
            instruments = self.tl.get_all_instruments()
            # print(instruments.head())  # for debugging, show first 5 rows
            if "name" in instruments.columns:
                symbols = instruments["name"].dropna().unique().tolist()
                return symbols
            else:
                return {'error': "No 'name' column in instruments data."}
        except Exception as e:
            return {'error': str(e)}
        
    def get_history_candles(self, symbol, interval, limit=100):
        try:
            instrument_id = self.tl.get_instrument_id_from_symbol_name(symbol)
            if not instrument_id:
                return {'error': f"Symbol {symbol} not found."}

            interval_map = {
                '1m': 'M1',
                '5m': 'M5',
                '15m': 'M15',
                '30m': 'M30',
                '1h': 'H1',
                '4h': 'H4',
                '1d': 'D1',
                '1w': 'W1',
                '1mo': 'MN1'
            }

            tl_interval = interval_map.get(interval)
            if not tl_interval:
                return {'error': f"Interval {interval} is not supported."}

            end_ts = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
            start_ts = end_ts - (limit * {
                'M1': 60 * 1000,
                'M5': 5 * 60 * 1000,
                'M15': 15 * 60 * 1000,
                'M30': 30 * 60 * 1000,
                'H1': 60 * 60 * 1000,
                'H4': 4 * 60 * 60 * 1000,
                'D1': 24 * 60 * 60 * 1000,
                'W1': 7 * 24 * 60 * 60 * 1000,
                'MN1': 30 * 24 * 60 * 60 * 1000,
            }[tl_interval])

            candles = self.tl.get_market_depth(instrument_id, start_timestamp=start_ts, end_timestamp=end_ts, granularity=tl_interval)

            if candles.empty:
                return []

            # Convert DataFrame to list of dicts
            candle_list = []
            for _, row in candles.iterrows():
                candle = {
                    'time': timezone.make_aware(datetime.fromtimestamp(row['timestamp'] / 1000.0), timezone.utc),
                    'open': str(row['open']),
                    'high': str(row['high']),
                    'low': str(row['low']),
                    'close': str(row['close']),
                    'volume': str(row['volume']),
                }
                candle_list.append(candle)

            return candle_list
        except Exception as e:
            return {'error': str(e)}
