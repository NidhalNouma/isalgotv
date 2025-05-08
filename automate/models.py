from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django_cryptography.fields import encrypt
from django.contrib.postgres.fields import JSONField 
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from profile_user.models import User_Profile

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

import json
from django.utils import timezone
import shortuuid


def generate_short_unique_id(prefix, id):
    short_id = shortuuid.ShortUUID().random(length=14 - len(prefix) - 1)  # Subtract the length of prefix and the hyphen
    return f"{prefix}{id}x{short_id}"


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
        # Add other brokers here
    ]

    TYPE = [
        ("D", "Derivatives"),
        ("F", "Futures"),
        ("S", "Spot"),
        ("U", "USD@M"),
        ("C", "COIN@M"),
        ("UC", "USD@C"),
    ]


    broker_type = models.CharField(max_length=20, choices=BROKER_TYPES)

    type = models.CharField(max_length=2, choices=TYPE, default="S")

    name = models.CharField(max_length=100)
    apiKey = models.CharField(max_length=150)
    secretKey = encrypt(models.CharField(max_length=150))

    active = models.BooleanField(default=True)

    pass_phrase = models.CharField(max_length=150, blank=True, null=True)  # Optional for brokers that need it

    custom_id = models.CharField(max_length=30, default="")
    
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    subscription_id = models.CharField(max_length=100, blank=False)

    def save(self, *args, **kwargs):        # Ensure subscription_id is provided
        if not self.subscription_id:
            raise ValueError("Subscription is required to create a Crypto Broker Account.")
        
        # Save the instance first to get an ID if it's a new record
        creating = self._state.adding  # True if the instance is being created
        super(CryptoBrokerAccount, self).save(*args, **kwargs)

        # Only generate a custom_id if it's a new record and custom_id is not set
        if creating and self.custom_id == "":
            self.custom_id = generate_short_unique_id(self.broker_type, self.id)
            super(CryptoBrokerAccount, self).save(*args, **kwargs) 
            

# Forex brokers ----------------------------------------------------------------

class ForexBrokerAccount(models.Model):
    BROKER_TYPES = [
        ("tradelocker", "TradeLocker"),
        ("metatrader4", "Metatrader 4"),
        ("metatrader5", "Metatrader 5"),
        ("dxtrade", "DXTrade"),
    ]

    TYPE = [
        ("D", "Demo"),
        ("L", "Live"),
    ]

    broker_type = models.CharField(max_length=20, choices=BROKER_TYPES)

    type = models.CharField(max_length=1, choices=TYPE, default="D")


    name = models.CharField(max_length=100)
    username = models.CharField(max_length=150, blank=True, null=True) 
    password = encrypt(models.CharField(max_length=150))
    server = models.CharField(max_length=150)
    
    account_api_id = models.CharField(max_length=30, default="")

    custom_id = models.CharField(max_length=30, default="")
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    subscription_id = models.CharField(max_length=100, blank=False)


    def save(self, *args, **kwargs):
        if not self.subscription_id:
            raise ValueError("Subscription is required to create a Forex Broker Account.")
        
        # Save the instance first to get an ID if it's a new record
        creating = self._state.adding  # True if the instance is being created
        super(ForexBrokerAccount, self).save(*args, **kwargs)

        # Only generate a custom_id if it's a new record and custom_id is not set
        if creating and self.custom_id == "":
            self.custom_id = generate_short_unique_id(self.broker_type, self.id)
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

    custom_id = models.CharField(max_length=40)
    order_id = models.CharField(max_length=40)

    symbol = models.CharField(max_length=40)
    volume = models.DecimalField(decimal_places=10, max_digits=40, default=0)
    remaining_volume = models.DecimalField(decimal_places=10, max_digits=40, default=0)

    entry_price = models.DecimalField(decimal_places=10, max_digits=40, default=0)
    exit_price = models.DecimalField(decimal_places=10, max_digits=40, default=0)

    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(default=timezone.now)

    fees = models.DecimalField(decimal_places=6, max_digits=40, default=0)
    profit = models.DecimalField(decimal_places=6, max_digits=40, default=0)

    side = models.CharField(max_length=1, choices=TYPE)
 
    trade_type = models.CharField(max_length=1, default="S")
    status = models.CharField(max_length=1, choices=STATUS, default='O')

    fills = models.JSONField(default=list, blank=True, validators=[validate_fills])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    account = GenericForeignKey('content_type', 'object_id')

    def add_fill(self, fill_data):
        """
        Append a new fill entry to the fills JSONField. fill_data can be a dict or JSON string.
        Updates remaining_volume and status based on the 'volume' field.
        """

        # Parse JSON string if necessary
        if isinstance(fill_data, str):
            try:
                fill_dict = json.loads(fill_data)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string for fill_data")
        elif isinstance(fill_data, dict):
            fill_dict = fill_data.copy()
        else:
            raise TypeError("fill_data must be a dict or JSON string")

        # Ensure timestamp
        if "timestamp" not in fill_dict or not fill_dict["timestamp"]:
            fill_dict["timestamp"] = timezone.now().isoformat()

        try:
            # Append new fill record
            self.fills = self.fills or []
            self.fills.append(fill_dict)

            # self.save(update_fields=["fills"])
        except Exception as e:
            print("Error saving trade fills ", e)

    def pre_save_adjustments(self):
        try:
            if self.status != 'O':
                from .functions.alerts_logs_trades import get_trade_data
                trade_data = get_trade_data(self.account, self)
                # print(trade_data)
                if trade_data:
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
                    

                    if self.status == 'P':
                        self.add_fill(trade_data)
                
        except Exception as e:
            print(e)
            pass

    def save(self, *args, **kwargs):
        # Run adjustments before saving
        self.pre_save_adjustments()
        super(TradeDetails, self).save(*args, **kwargs)

class LogMessage(models.Model):
    STATUS = [
        ("E", "Error"),
        ("S", "Success"),
    ]

    response_status = models.CharField(max_length=1, choices=STATUS)

    alert_message = models.TextField()
    response_message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    trade = models.ForeignKey(TradeDetails, on_delete=models.CASCADE, related_name="Trade", blank=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

