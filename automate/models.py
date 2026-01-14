from django.db import IntegrityError, models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django_cryptography.fields import encrypt
from django.contrib.postgres.fields import JSONField 
from django.core.exceptions import ValidationError

from decimal import Decimal, InvalidOperation

from profile_user.models import User_Profile
from strategies.models import Strategy
from performance.models import AccountPerformance

import json
from django.utils import timezone
import shortuuid

def generate_short_unique_id(prefix, id, sepparator='x'):
    max_length = 14 - len(prefix) - 1  # Subtract length of prefix and hyphen
    if max_length < 6:  # Ensure there's enough space for uniqueness
        max_length = 6
    short_id = shortuuid.ShortUUID().random(length=max_length)  
    return f"{prefix}{id}{sepparator}{short_id}"


# Crypto brokers ----------------------------------------------------------------

class CryptoBrokerAccount(models.Model):
    BROKER_TYPES = [
        ("binance", "Binance"),
        ("binanceus", "Binance US"),
        ("bitget", "Bitget"),
        ("bybit", "Bybit"),
        ("mexc", "MEXC"),
        ("bingx", "Bingx"),
        ("bitmex", "Bitmex"),
        ("bitmart", "BitMart"),
        ("crypto", "Crypto.com"),
        ("kucoin", "Kucoin"),
        ("kraken", "Kraken"),
        ("okx", "Okx"),
        ("coinbase", "Coinbase"),
        ("apex", "Apex omni"),
        ('hyperliquid', 'Hyperliquid'),
        # Add other brokers here
    ]

    TYPE = [
        ("D", "Derivatives"),
        ("P", "Perps"),
        ("F", "Futures"),
        ("S", "Spot"),
        ("U", "USD@M"),
        ("C", "COIN@M"),
        ("UC", "USD@C"),
    ]

    broker_type = models.CharField(max_length=20, choices=BROKER_TYPES)
    type = models.CharField(max_length=2, choices=TYPE, default="S")

    name = models.CharField(max_length=150)
    apiKey = models.CharField(max_length=200)
    secretKey = encrypt(models.CharField(max_length=350))
    pass_phrase = models.CharField(max_length=300, blank=True, null=True)  # Optional for brokers that need it

    active = models.BooleanField(default=True)
    custom_id = models.CharField(max_length=120, default="")
    public_id = models.CharField(max_length=120, default="")

    additional_info = models.JSONField(default=dict, blank=True)
    
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    subscription_id = models.CharField(max_length=100, blank=False)

    _performances = GenericRelation(
        "performance.AccountPerformance",
        content_type_field="content_type",
        object_id_field="object_id"
    )

    @property
    def performance(self):
        """Get the single AccountPerformance for this account."""
        return self._performances.first()

    def generate_public_id(self, replace=False, save=True):
        if self.public_id == "" or replace:
            self.public_id = generate_short_unique_id("pubc", self.id, 'i')
            if save:
                self.save()
                
    def generate_custom_id(self, replace=False, save=True):
        if self.custom_id == "" or replace:
            self.custom_id = generate_short_unique_id(self.broker_type, self.id)
            if save:
                self.save()

    def save(self, *args, **kwargs):        # Ensure subscription_id is provided
        if not self.subscription_id:
            raise ValueError("Subscription is required to create a Crypto Broker Account.")
        
        # Save the instance first to get an ID if it's a new record
        creating = self._state.adding  # True if the instance is being created
        super(CryptoBrokerAccount, self).save(*args, **kwargs)

        # Only generate a custom_id if it's a new record and custom_id is not set
        if creating:
            self.generate_custom_id(save=False)
            self.generate_public_id(save=False)
            super(CryptoBrokerAccount, self).save(*args, **kwargs) 

# Forex brokers ----------------------------------------------------------------

class ForexBrokerAccount(models.Model):
    BROKER_TYPES = [
        ("tradelocker", "TradeLocker"),
        ("metatrader4", "Metatrader 4"),
        ("metatrader5", "Metatrader 5"),
        ("ninjatrader", "NinjaTrader"),
        ("dxtrade", "DXTrade"),
        ("ctrader", "CTrader"),
        ("deriv", "Deriv"),
        ("hankotrade", "HankoTrade"),
        ("tradestation", "TradeStation"),
        ("alpaca", "Alpaca"),
        ('tastytrade', 'Tastytrade'),
    ]

    TYPE = [
        ("D", "Demo"),
        ("L", "Live"),
    ]

    broker_type = models.CharField(max_length=20, choices=BROKER_TYPES)
    type = models.CharField(max_length=1, choices=TYPE, default="D")

    name = models.CharField(max_length=150)
    username = models.CharField(max_length=600, blank=True, null=True) 
    password = encrypt(models.CharField(max_length=600))
    server = models.CharField(max_length=150)
    account_api_id = models.CharField(max_length=150, default="")

    active = models.BooleanField(default=True)
    custom_id = models.CharField(max_length=120, default="")
    public_id = models.CharField(max_length=120, default="")

    additional_info = models.JSONField(default=dict, blank=True)

    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    subscription_id = models.CharField(max_length=100, blank=False)
    
    _performances = GenericRelation(
        "performance.AccountPerformance",
        content_type_field="content_type",
        object_id_field="object_id"
    )

    @property
    def performance(self):
        """Get the single AccountPerformance for this account."""
        return self._performances.first()

    def generate_public_id(self, replace=False, save=True):
        if self.public_id == "" or replace:
            self.public_id = generate_short_unique_id("pubf", self.id, 'i')
            if save:
                self.save()

    def generate_custom_id(self, replace=False, save=True):
        if self.custom_id == "" or replace:
            self.custom_id = generate_short_unique_id(self.broker_type, self.id)
            if save:
                self.save()

    def save(self, *args, **kwargs):
        if not self.subscription_id:
            raise ValueError("Subscription is required to create a Forex Broker Account.")
        
        # Save the instance first to get an ID if it's a new record
        creating = self._state.adding  # True if the instance is being created
        super(ForexBrokerAccount, self).save(*args, **kwargs)

        # Only generate a custom_id if it's a new record and custom_id is not set
        if creating:
            self.generate_custom_id(save=False)
            self.generate_public_id(save=False)
            super(ForexBrokerAccount, self).save(*args, **kwargs) 
        
# Trades and Logs ----------------------------------------------------------------

def validate_fills(value):
    """
    Ensure fills is a list of objects, each containing the required keys.
    """
    if not isinstance(value, list):
        raise ValidationError("Fills must be a list of objects")
    required_keys = {"close_price", "volume", "close_time", "profit", "fees"}

    for idx, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValidationError(f"Fill at index {idx} must be an object")
        missing = required_keys - item.keys()
        extra = set(item.keys()) - required_keys
        if missing:
            raise ValidationError(f"Fill at index {idx} missing keys: {', '.join(missing)}")
        if extra:
            raise ValidationError(f"Fill at index {idx} has unexpected keys: {', '.join(extra)}")


class TradeDetails(models.Model):

    TYPE = [
        ("B", "Buy"),
        ("S", "Sell"),
    ]

    STATUS = [
        ("O", "OPEN"),
        ("P", "PARTIALLY_CLOSED"),
        ("C", "CLOSED"),
    ]

    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trades'
    )

    custom_id = models.CharField(max_length=40)
    order_id = models.CharField(max_length=40)
    closed_order_id = models.CharField(max_length=40, default='')

    currency = models.CharField(max_length=10, default='')

    symbol = models.CharField(max_length=40)
    volume = models.DecimalField(decimal_places=10, max_digits=40, default=0)
    remaining_volume = models.DecimalField(decimal_places=10, max_digits=40, default=0)

    entry_price = models.DecimalField(decimal_places=10, max_digits=40, default=0)
    exit_price = models.DecimalField(decimal_places=10, max_digits=40, default=0)

    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(default=timezone.now)

    fees = models.DecimalField(decimal_places=10, max_digits=40, default=0)
    profit = models.DecimalField(decimal_places=10, max_digits=40, default=0)

    @property
    def net_profit(self):
        return self.profit - abs(self.fees)

    side = models.CharField(max_length=1, choices=TYPE)
 
    trade_type = models.CharField(max_length=2, default="S")
    status = models.CharField(max_length=1, choices=STATUS, default='O')

    fills = models.JSONField(default=list, blank=True, validators=[validate_fills])
    additional_info = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    account = GenericForeignKey('content_type', 'object_id')

    def get_total_filled_volume(self):
        """
        Calculates the total filled volume across all fills.
        Returns a Decimal for precision.
        """
        total_volume = Decimal('0')
        if not self.fills:
            return total_volume

        for fill in self.fills:
            try:
                volume = Decimal(str(fill.get('volume', 0)))
                total_volume += volume
            except (TypeError, InvalidOperation):
                continue

        return total_volume

    def add_fill(self, trade_data):
        """
        Append a new fill entry to the fills JSONField. fill_data can be a dict or JSON string.
        Updates remaining_volume and status based on the 'volume' field.
        """

        # Parse JSON string if necessary
        if isinstance(trade_data, str):
            try:
                trade_data = json.loads(trade_data)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string for fill_data(trade_data)")
        elif isinstance(trade_data, dict):
            trade_data = trade_data.copy()
        else:
            raise TypeError("trade_data must be a dict or JSON string")

        try:
            self.exit_time = trade_data.get('close_time', timezone.now)

            close_price = trade_data.get('close_price', 0)
            profit = trade_data.get('profit', 0)
            fees = trade_data.get('fees', 0)

            try:
                self.exit_price = Decimal(str(close_price))
                self.profit = self.profit + Decimal(str(profit))
                self.fees = self.fees + Decimal(str(fees))
            except (TypeError, ValueError, InvalidOperation):
                self.exit_price = Decimal('0')
                self.profit = self.profit + Decimal('0')
                self.fees = self.fees + Decimal('0')
                            # Append new fill record
            self.fills = self.fills or []
            self.fills.append(trade_data)

            if not self.currency:
                currency = trade_data.get('currency', None)
                if currency:
                    self.currency = currency

            # self.save(update_fields=["fills"])
        except Exception as e:
            print("Error saving trade fills ", e)

    def pre_save_adjustments(self):
        try:
            if self.status != 'O':
                trade = self.closed_trade_details

                if trade:
                    trade_response = trade
                else:
                    from .functions.alerts_logs_trades import get_trade_data
                    trade_response = get_trade_data(self.account, self)
                    
                # print(trade_response)
                if trade_response:
                    if isinstance(trade_response, list):
                        if len(trade_response) > len(self.fills):
                            self.fills = []

                            self.profit = 0
                            self.fees = 0
                            # trade_data is an “array” of fills or orders
                            for data in trade_response:
                                # handle each dict in the list
                                self.add_fill(data)

                    else:
                        trade_data = trade_response 
                        self.add_fill(trade_data)
                
        except Exception as e:
            print('Pre adjustment trade error: ', e)
            pass

    def save(self, *args, **kwargs):
        try:
            if Decimal(self.remaining_volume) <= 0:
                self.status = 'C'
            elif Decimal(self.remaining_volume) < Decimal(self.volume):
                self.status = 'P'
            else:
                self.status = 'O'

            # Run adjustments before saving
            self.pre_save_adjustments()

            filled_volume = Decimal(self.volume) - Decimal(self.get_total_filled_volume())
            if filled_volume < Decimal(self.remaining_volume):
                self.remaining_volume = filled_volume

            if Decimal(self.remaining_volume) <= 0:
                self.status = 'C'

            super(TradeDetails, self).save(*args, **kwargs)
        except Exception as e:
            print('saving trade error: ', e)
            pass 

class LogMessage(models.Model):
    STATUS = [
        ("E", "Error"),
        ("S", "Success"),
        ("I", "Info"),
        ("W", "Warning"),
    ]

    response_status = models.CharField(max_length=1, choices=STATUS)

    alert_message = models.TextField()
    response_message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    latency = models.FloatField(blank=True, default=0.0, help_text="Latency in seconds")
    trade_latency = models.FloatField(blank=True, default=0.0, help_text="Trade Latency in seconds")

    trade = models.ForeignKey(TradeDetails, on_delete=models.CASCADE, related_name="Trade", blank=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
