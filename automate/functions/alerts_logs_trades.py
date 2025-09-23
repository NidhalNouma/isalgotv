from django.contrib.contenttypes.models import ContentType

from decimal import Decimal
from django.utils import timezone
from django.db import transaction
import inspect

from automate.models import *

from automate.functions.brokers.binance_cl import BinanceClient
from automate.functions.brokers.binance_us import BinanceUSClient
from automate.functions.brokers.bitget import BitgetClient
from automate.functions.brokers.bybit import BybitClient
from automate.functions.brokers.mexc import MexcClient
from automate.functions.brokers.crypto import CryptoComClient
from automate.functions.brokers.bingx import BingxClient
from automate.functions.brokers.bitmart import BitmartClient
from automate.functions.brokers.kucoin import KucoinClient
from automate.functions.brokers.coinbase import CoinbaseClinet

from automate.functions.brokers.trade_locker import TradeLockerClient
from automate.functions.brokers.metatrader import MetatraderClient
from automate.functions.brokers.dxtrade import DxtradeClient
from automate.functions.brokers.ninjatrader import NinjatraderClient

# Map broker types to their client classes
CLIENT_CLASSES = {
    'binance': BinanceClient,
    'binanceus': BinanceUSClient,
    'bitget': BitgetClient,
    'bybit': BybitClient,
    'mexc': MexcClient,
    'crypto': CryptoComClient,
    'bingx': BingxClient,
    'bitmart': BitmartClient,
    'kucoin': KucoinClient,
    'coinbase': CoinbaseClinet,

    'tradelocker': TradeLockerClient,
    'ninjatrader': NinjatraderClient,
    'dxtrade': DxtradeClient,
    'metatrader4': MetatraderClient,
    'metatrader5': MetatraderClient,
}

def check_crypto_credentials(broker_type, api_key, api_secret, phrase, account_type="S"):
    print(f"Checking crypto credentials for {broker_type}")
    
    # Parameters required by each check_credentials method
    CREDENTIAL_PARAMS = {
        'binance': {},
        'binanceus': {},
        'bitget': {'passphrase': phrase},
        'bybit': {},
        'mexc': {},
        'crypto': {},
        'bingx': {},
        'bitmart': {'passphrase': phrase},
        'kucoin': {'passphrase': phrase},
        'coinbase': {},
    }

    client_cls = CLIENT_CLASSES.get(broker_type)
    if client_cls is None:
        raise Exception(f"Unsupported broker type: {broker_type}")
    params = CREDENTIAL_PARAMS[broker_type]
    return client_cls.check_credentials(api_key, api_secret, account_type=account_type, **params)

def check_forex_credentials(broker_type, username, password, server, type="D"):
    
    if broker_type == 'tradelocker':
        return TradeLockerClient.check_credentials(username, password, server, type)
    elif broker_type == 'metatrader4':
        return MetatraderClient.check_credentials(username, username, password, server, "mt4")
    elif broker_type == 'metatrader5':
        return MetatraderClient.check_credentials(username, username, password, server, "mt5")
    elif broker_type == 'ninjatrader':
        return NinjatraderClient.check_credentials(username, password, server, type)
    elif broker_type == 'dxtrade':
        return DxtradeClient.check_credentials(username, password, server)
    else:
        raise Exception("Unsupported broker type.")

    
def open_trade_by_account(account, symbol, side, volume, custom_id):
    try:
        broker_type = account.broker_type
        
        client_cls = CLIENT_CLASSES.get(broker_type)
        if client_cls is None:
            raise Exception(f"Unsupported broker type: {broker_type}")
        
        client = client_cls(account=account)
        return client.open_trade(symbol, side, volume, custom_id)
    except Exception as e:
        print('open trade error: ', str(e))
        raise e
    
def close_trade_by_account(account, trade_to_close, symbol, side, volume_close):
    try:
        broker_type = account.broker_type
        
        client_cls = CLIENT_CLASSES.get(broker_type)
        if client_cls is None:
            raise Exception(f"Unsupported broker type: {broker_type}")
        
        client = client_cls(account=account, current_trade=trade_to_close)
        return client.close_trade(symbol, side, volume_close)
    except Exception as e:
        print('close trade error: ', str(e))
        raise e

def get_trade_data(account, trade):
    try:
        broker_type = account.broker_type

        client_cls = CLIENT_CLASSES.get(broker_type)
        if client_cls is None:
            raise Exception(f"Unsupported broker type: {broker_type}")
        
        client = client_cls(account=account)
        return client.get_final_trade_details(trade)
    except Exception as e:
        print('close trade error: ', str(e))
        raise e
    
def save_log(response_status, alert_message, response_message, account, trade = None):
    if type(account) == CryptoBrokerAccount:
        log = LogMessage.objects.create(
            response_status=response_status,
            alert_message=alert_message,
            response_message=response_message,
            trade=trade,
            
            content_type=ContentType.objects.get_for_model(CryptoBrokerAccount),
            object_id=account.id
        )
    elif type(account) == ForexBrokerAccount:
        log = LogMessage.objects.create(
            response_status=response_status,
            alert_message=alert_message,
            response_message=response_message,
            trade=trade,
            
            content_type=ContentType.objects.get_for_model(ForexBrokerAccount),
            object_id=account.id
        )
    else:
        raise Exception("Account model not supported.")


    return log

def save_new_trade(custom_id, side, opend_trade, account, strategy_id):
    order_id = opend_trade.get('order_id') 
    symbol = opend_trade.get('symbol')
    volume = opend_trade.get('qty')
    price = opend_trade.get('price', 0)
    time = opend_trade.get('time', timezone.now())
    currency = opend_trade.get('currency', '')
    fees = opend_trade.get('fees', 0)
    closed_order_id = opend_trade.get('closed_order_id', '')

    t_side = "B" if str.lower(side) == "buy" else "S"
    
    if isinstance(account, (CryptoBrokerAccount, ForexBrokerAccount)):
        content_type = ContentType.objects.get_for_model(account.__class__)
        
        trade = TradeDetails.objects.create(
            custom_id=custom_id,
            order_id=order_id,
            symbol=symbol,
            side=t_side,
            volume=volume,
            remaining_volume=volume,
            entry_price=price,
            entry_time=time,
            currency=currency,
            fees=fees,
            closed_order_id=closed_order_id,
            trade_type=getattr(account, 'type', None),
            content_type=content_type,
            object_id=account.id,
            strategy=Strategy.objects.filter(id=strategy_id).first()
        )

    else:
        raise ValueError(f"Unsupported account model: {type(account)}")
    
    return trade

def get_trade(custom_id, symbol, side, account, strategy_id):
    t_side = "B" if str.lower(side) == "buy" else "S"

    content_type = ContentType.objects.get_for_model(account.__class__)

    trade = TradeDetails.objects.filter(
        custom_id=custom_id,
        symbol=symbol,
        side=t_side,
        strategy_id=strategy_id,
        content_type=content_type,
        object_id=account.id
    ).last()

    return trade

def get_trade_for_update(custom_id, symbol, side, account, strategy_id):
    t_side = "B" if str.lower(side) == "buy" else "S"

    content_type = ContentType.objects.get_for_model(account.__class__)

    if inspect.iscoroutinefunction(get_trade_for_update):
        async def _async_inner():
            async with transaction.atomic():
                return await TradeDetails.objects.select_for_update().filter(
                    custom_id=custom_id,
                    symbol=symbol,
                    side=t_side,
                    strategy_id=strategy_id,
                    content_type=content_type,
                    object_id=account.id
                ).alast()
        return _async_inner()
    else:
        with transaction.atomic():
            trade = TradeDetails.objects.select_for_update().filter(
                custom_id=custom_id,
                symbol=symbol,
                side=t_side,
                strategy_id=strategy_id,
                content_type=content_type,
                object_id=account.id
            ).last()

    return trade

def update_trade_after_close(trade, closed_volume, closed_trade):

    closed_volume = closed_trade.get('qty', closed_volume)
    price = closed_trade.get('price', 0)
    closed_order_id = closed_trade.get('closed_order_id', '')

    closed_trade_details = closed_trade.get('trade_details', None)

    trade.closed_trade_details = closed_trade_details

    trade.exit_price = float(price)
    trade.closed_order_id = closed_order_id
    trade.remaining_volume = float(trade.remaining_volume) - float(closed_volume)
    trade.save()

    return trade

def volume_to_close(trade, partial):
    if partial:
        volume_to_close = Decimal(trade.volume) * Decimal(partial) / Decimal(100)
        print("Volume to close:", volume_to_close, 'from', trade.remaining_volume)
        
        if volume_to_close > Decimal(trade.remaining_volume):
            volume_to_close = Decimal(trade.remaining_volume)
        
        if Decimal(trade.remaining_volume) <= 0:
            raise Exception("No volume left to close.")
        
        # Return as a fixed-point decimal string
        return format(volume_to_close, 'f')
    else:
        # Return the full volume as a fixed-point decimal string
        return format(Decimal(trade.volume), 'f')