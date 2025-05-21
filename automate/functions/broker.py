from django.utils import timezone
from datetime import datetime

from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP



class BrokerClient:

    @staticmethod
    def check_credentials(**kwargs):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def open_trade(self, **kwargs):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def close_trade(self, **kwargs):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_order_info(self, symbol, order_id):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_decimals_from_step(self, size_str):
        """
        Determine the number of decimal places allowed by a step size,
        stripping any trailing zeros in the step definition.
        """
        d = Decimal(size_str)
        # Normalize to remove any trailing zeros (e.g., '0.10000000' -> '0.1')
        d_norm = d.normalize()
        exp = d_norm.as_tuple().exponent
        return max(-exp, 0)

    def convert_timestamp(self, timestamp):
        try:
            print("Original timestamp:", timestamp)
            ts_s = int(timestamp) / 1000  
            dt_naive = datetime.fromtimestamp(ts_s)
            dt_aware = timezone.make_aware(dt_naive, timezone=timezone.utc)
            print("Converted timestamp:", dt_aware)
            return dt_aware
        except Exception as e:
            return timezone.now()


    def get_final_trade_details(self, trade, order_id=None):
        if not order_id:
            trade_id = trade.closed_order_id or trade.order_id
        else:
            trade_id = order_id

        try:
            result = self.get_order_info(trade.symbol, trade_id)

            if result:
                # Convert price and volume to Decimal for accurate calculation
                try:
                    price_dec = Decimal(str(result.get('price', '0')))
                except (InvalidOperation, ValueError):
                    price_dec = Decimal('0')
                try:
                    volume_dec = Decimal(str(result.get('volume', '0')))
                except (InvalidOperation, ValueError):
                    volume_dec = Decimal('0')


                side_upper = trade.side.upper()

                if price_dec != 0:
                    if side_upper in ("B", "BUY"):
                        profit = (price_dec - Decimal(str(trade.entry_price))) * volume_dec
                    elif side_upper in ("S", "SELL"):
                        profit = (Decimal(str(trade.entry_price)) - price_dec) * volume_dec
                    else:
                        profit = Decimal("0")
                else:
                    profit = Decimal("0")

                res = {
                    'order_id': str(result.get('order_id')),
                    'symbol': str(result.get('symbol')),
                    'volume': str(result.get('volume')),
                    'side': str(result.get('side')),

                    'open_price': str(trade.entry_price),
                    'close_price': str(result.get('price')),

                    'open_time': str(trade.entry_time),
                    'close_time': str(result.get('time')), 

                    'fees': str(result.get('fees')), 

                    'profit': str(profit),

                    'additional_info': str(result.get('additional_info'))
                }

                return res
            
            return None

        except Exception as e:
            print("Error:", e)
            return None
