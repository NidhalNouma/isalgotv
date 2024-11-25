
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User
from profile_user.models import User_Profile

import shortuuid

def generate_short_unique_id(prefix, id):
    short_id = shortuuid.ShortUUID().random(length=14 - len(prefix) - 1)  # Subtract the length of prefix and the hyphen
    return f"{prefix}{id}x{short_id}"


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

    custom_id = models.CharField(max_length=20)
    order_id = models.CharField(max_length=20)
    symbol = models.CharField(max_length=12)

    volume = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    remaining_volume = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    profit = models.DecimalField(decimal_places=2, max_digits=20, default=0)

    side = models.CharField(max_length=1, choices=TYPE)
 
    trade_type = models.CharField(max_length=6)

    status = models.CharField(max_length=1, choices=STATUS, default='O')


    created_at = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


class LogMessage(models.Model):
    TYPE = [
        ("E", "Error"),
        ("S", "Success"),
    ]

    type = models.CharField(max_length=1, choices=TYPE)

    trade = models.ForeignKey(TradeDetails, on_delete=models.DO_NOTHING, related_name="logs")

    alert_message = models.TextField()
    response_message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


class CryptoBrokerAccount(models.Model):
    BROKER_TYPES = [
        ("binance", "Binance"),
        ("bitget", "Bitget"),
        ("bybit", "Bybit"),
        ("bingx", "Bingx"),
        ("bitmex", "Bitmex"),
        ("bitmart", "BitMart"),
        # Add other brokers here
    ]

    TYPE = [
        ("D", "Derivatives"),
        ("F", "Futures"),
        ("S", "Spot"),
        ("U", "USD@M"),
        ("C", "COIN@M"),
    ]


    broker_type = models.CharField(max_length=20, choices=BROKER_TYPES)

    type = models.CharField(max_length=1, choices=TYPE, default="S")

    name = models.CharField(max_length=100)
    apiKey = models.CharField(max_length=150)
    secretKey = models.CharField(max_length=150)

    active = models.BooleanField(default=True)

    pass_phrase = models.CharField(max_length=150, blank=True, null=True)  # Optional for brokers that need it

    # default_symbol = models.CharField(max_length=30, default="")
    # default_volume = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    trades = GenericRelation(TradeDetails) 
    logs = GenericRelation(LogMessage) 

    custom_id = models.CharField(max_length=30, default="")
    
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        # Save the instance first to get an ID if it's a new record
        creating = self._state.adding  # True if the instance is being created
        super(CryptoBrokerAccount, self).save(*args, **kwargs)

        # Only generate a custom_id if it's a new record and custom_id is not set
        if creating and self.custom_id == "":
            self.custom_id = generate_short_unique_id(self.broker_type, self.id)
            super(CryptoBrokerAccount, self).save(*args, **kwargs) 

