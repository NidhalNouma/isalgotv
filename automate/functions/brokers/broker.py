from django.utils import timezone
import abc

from datetime import datetime

import time
import hmac
import hashlib
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP

from .types import *

class BrokerClient(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def check_credentials(**kwargs):
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abc.abstractmethod
    def open_trade(self, **kwargs) -> OpenTrade:
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abc.abstractmethod
    def close_trade(self, **kwargs) -> CloseTrade:
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abc.abstractmethod
    def get_order_info(self, symbol, order_id) -> OrderInfo:
        raise NotImplementedError("This method should be implemented by subclasses.")


    def get_decimals_from_step(self, size_str):
        """
        Returns the number of decimal places in the given step size string.
        For example:
          - '0.03' -> 2
          - '0.123' -> 3
        Returns 8 if the input is invalid.
        """
        try:
            d = Decimal(str(size_str))
            d_norm = d.normalize()
            exp = d_norm.as_tuple().exponent
            return max(-exp, 0)
        except Exception:
            return 8

    def convert_timestamp(self, timestamp):
        try:
            ts_s = int(timestamp) / 1000  
            dt_naive = datetime.fromtimestamp(ts_s)
            dt_aware = timezone.make_aware(dt_naive, timezone=timezone.utc)
            return dt_aware
        except Exception as e:
            return timezone.now()


    def get_final_trade_details(self, trade, order_id=None) -> TradeDetails:
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

                profit = result.get('profit')

                if profit in [None, 'None']:
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
                }

                if result.get('currency'):
                    res['currency'] = result.get('currency')
                if result.get('additional_info'):
                    res['additional_info'] = str(result.get('additional_info'))

                return res
            
            return None

        except Exception as e:
            print("Error:", e)
            return None


class CryptoBrokerClient(BrokerClient, abc.ABC):
    
    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        # Support either a Django account object or explicit credentials
        if account is not None:
            self.api_key = account.apiKey
            self.api_secret = account.secretKey
            self.passphrase = account.pass_phrase
            self.account = account
            self.account_type = getattr(account, 'type', account_type)
        else:
            self.api_key = api_key
            self.api_secret = api_secret
            self.account_type = account_type
            self.passphrase = passphrase
        self.current_trade = current_trade

    def _get_timestamp(self):
        return int(time.time() * 1000)

    def create_signature(self, query_string):
        return hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    def calculate_fees(self, symbol, price, fees, fee_currency=''):
        try:
            fees = Decimal(str(fees))
            if fee_currency:
                sym_info = self.get_exchange_info(symbol)
                if str(fee_currency) == sym_info.get('base_asset'):
                    _price = Decimal(str(price))
                    fees = fees * _price
        except (InvalidOperation, ValueError):
            pass
        
        return abs(fees)

    @abc.abstractmethod
    def get_exchange_info(self, symbol: str) -> ExchangeInfo:
        """
        Fetches exchange information for a given symbol.

        This method should be implemented by subclasses.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    

    @abc.abstractmethod
    def get_account_balance(self) -> AccountBalance:
        """
        Fetches the account balance.

        This method should be implemented by subclasses.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    

    def adjust_trade_quantity(self, exchange_info, side, quote_order_qty) -> float:
        """
        Adjusts the trade quantity based on the exchange's step size and the order side.

        :param exchange_info: Exchange information containing step size.
        :param side: The side of the order ('BUY' or 'SELL').
        :param quote_order_qty: The desired order quantity in quote currency.
        :return: Adjusted order quantity.
        """

        try:
            base_asset, quote_asset = exchange_info.get("base_asset"), exchange_info.get("quote_asset")
            if not base_asset or not quote_asset:
                raise ValueError("Invalid symbol format or exchange info not found.")

            balances = self.get_account_balance()

            if not balances:
                raise ValueError("Failed to retrieve account balances.")
            
            base_balance = balances.get(base_asset, {}).get('available', 0)
            quote_balance = balances.get(quote_asset, {}).get('available', 0)

            base_decimals = exchange_info.get('base_decimals') 
            quote_decimals = exchange_info.get('quote_decimals') 

            print("Base asset:", base_asset, base_decimals)
            print("Quote asset:", quote_asset, quote_decimals)

            print("Base balance:", base_balance)
            print("Quote balance:", quote_balance)

            try:
                precision = int(base_decimals)
            except (TypeError, ValueError):
                precision = 8  # fallback precision
            quant = Decimal(1).scaleb(-precision)  

            if self.account_type == "S":
                if side.upper() == "BUY":
                    if float(quote_balance) <= 0:
                        raise ValueError("Insufficient quote balance.")
                    
                    if self.account.broker_type =="bitget":
                        price = self.get_exchange_price(exchange_info.get('symbol'))
                        if price == 0:
                            raise ValueError("Price is zero, cannot calculate order quantity.")
                        # Calculate the maximum order quantity based on the quote balance

                        try:
                            precision = int(quote_decimals)
                        except (TypeError, ValueError):
                            precision = 8  # fallback precision
                        quant = Decimal(1).scaleb(-precision)  

                        order_qty = float(quote_order_qty) * price

                        qty_dec = Decimal(str(order_qty)).quantize(quant, rounding=ROUND_UP)
                        return format(qty_dec, f'.{precision}f')

                    qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                    return format(qty_dec, f'.{precision}f')
                
                elif side.upper() == "SELL":
                    # print("Base balance:", base_balance, "Quote order qty:", quote_order_qty)
                    if float(base_balance) <= 0:
                        raise ValueError("Insufficient base balance.")
                    
                    elif float(base_balance) < float(quote_order_qty):
                        # Format quantity to max base_decimals and return as string
                        qty_dec = Decimal(str(base_balance)).quantize(quant, rounding=ROUND_DOWN)
                        return format(qty_dec, f'.{precision}f')
                    # Format quantity to max base_decimals and return as string
                    qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                    return format(qty_dec, f'.{precision}f')
                
            elif self.account_type == "U":  # USDM Futures
                qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                return format(qty_dec, f'.{precision}f')
            
            elif self.account_type == "C":  # COINM Futures
                quant = 0
                qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                return format(qty_dec, f'.{precision}f')
            
            else:  # Futures

                qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                return format(qty_dec, f'.{precision}f')
            
            return quote_order_qty
        except Exception as e:
            raise ValueError(str(e))
        