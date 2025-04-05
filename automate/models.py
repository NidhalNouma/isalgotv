from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django_cryptography.fields import encrypt

from django.contrib.auth.models import User
from profile_user.models import User_Profile

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

    subscription_id = models.CharField(max_length=100, blank=True)

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


    subscription_id = models.CharField(max_length=100, blank=True)


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

    custom_id = models.CharField(max_length=30)
    order_id = models.CharField(max_length=30)

    symbol = models.CharField(max_length=30)
    volume = models.DecimalField(decimal_places=10, max_digits=30, default=0)
    remaining_volume = models.DecimalField(decimal_places=10, max_digits=30, default=0)

    entry_price = models.DecimalField(decimal_places=10, max_digits=30, default=0)
    exit_price = models.DecimalField(decimal_places=10, max_digits=30, default=0)

    profit = models.DecimalField(decimal_places=4, max_digits=30, default=0)

    side = models.CharField(max_length=1, choices=TYPE)
 
    trade_type = models.CharField(max_length=1, default="S")
    status = models.CharField(max_length=1, choices=STATUS, default='O')


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    account = GenericForeignKey('content_type', 'object_id')


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

