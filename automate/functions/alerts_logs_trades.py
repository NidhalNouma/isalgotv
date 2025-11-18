from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from decimal import Decimal
from django.utils import timezone
import time

from automate.models import *

from automate.functions.brokers.binance import BinanceClient
from automate.functions.brokers.binance_us import BinanceUSClient
from automate.functions.brokers.bitget import BitgetClient
from automate.functions.brokers.bybit import BybitClient
from automate.functions.brokers.mexc import MexcClient
from automate.functions.brokers.crypto import CryptoComClient
from automate.functions.brokers.bingx import BingxClient
from automate.functions.brokers.bitmart import BitmartClient
from automate.functions.brokers.kucoin import KucoinClient
from automate.functions.brokers.coinbase import CoinbaseClient
from automate.functions.brokers.okx import OkxClient
from automate.functions.brokers.kraken import KrakenClient
from automate.functions.brokers.apex import ApexClient
from automate.functions.brokers.hyperliquid import HyperliquidClient

from automate.functions.brokers.tradelocker import TradeLockerClient
from automate.functions.brokers.metatrader import MetatraderClient
from automate.functions.brokers.dxtrade import DxtradeClient
from automate.functions.brokers.ninjatrader import NinjatraderClient
from automate.functions.brokers.ctrader import CtraderClient
from automate.functions.brokers.acttrader import HankoTradeClient
from automate.functions.brokers.alpaca import AlpacaClient

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
    'coinbase': CoinbaseClient,
    'okx': OkxClient,
    'kraken': KrakenClient,
    'apex': ApexClient,
    'hyperliquid': HyperliquidClient,

    'tradelocker': TradeLockerClient,
    'alpaca': AlpacaClient,
    'ninjatrader': NinjatraderClient,
    'dxtrade': DxtradeClient,
    'ctrader': CtraderClient,
    'metatrader4': MetatraderClient,
    'metatrader5': MetatraderClient,
    'hankotrade': HankoTradeClient,
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
        'kraken': {},
        'okx': {'passphrase': phrase},
        'apex': {'passphrase': phrase},
        'edgex': {},
        'hyperliquid': {},
    }

    client_cls = CLIENT_CLASSES.get(broker_type)
    if client_cls is None:
        raise Exception(f"Unsupported broker type: {broker_type}")
    params = CREDENTIAL_PARAMS[broker_type]
    return client_cls.check_credentials(api_key, api_secret, account_type=account_type, **params)

def check_forex_credentials(broker_type, username, password, server, type="D", account_id=None):
    
    if broker_type == 'tradelocker':
        return TradeLockerClient.check_credentials(username, password, server, type, account_id=account_id)
    elif broker_type == 'metatrader4':
        return MetatraderClient.check_credentials(username, username, password, server, "mt4")
    elif broker_type == 'metatrader5':
        return MetatraderClient.check_credentials(username, username, password, server, "mt5")
    elif broker_type == 'ninjatrader':
        return NinjatraderClient.check_credentials(username, password, server, type)
    elif broker_type == 'dxtrade':
        return DxtradeClient.check_credentials(username, password, server)
    elif broker_type == 'ctrader':
        return CtraderClient.check_credentials(authorization_code=server, type=type)
    elif broker_type == 'hankotrade':
        return HankoTradeClient.check_credentials(username, password, type)
    elif broker_type == 'alpaca':
        return AlpacaClient.check_credentials(username=username, password=password, type=type)
    else:
        raise Exception("Unsupported broker type.")

    
def open_trade_by_account(account, symbol, side, volume, custom_id, opposit_trades=[]):
    try:
        broker_type = account.broker_type
        
        client_cls = CLIENT_CLASSES.get(broker_type)
        if client_cls is None:
            raise Exception(f"Unsupported broker type: {broker_type}")
        
        client = client_cls(account=account)

        closed_trades = client.close_opposite_trades(opposit_trades)
        trade = client.open_trade(symbol, side, volume, custom_id)

        return trade, closed_trades
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
    
def save_log(response_status, alert_message, response_message, account, latency_start, end_exe=None, trade=None):
    latency = time.perf_counter() - latency_start

    trade_latency = 0
    if end_exe:
        trade_latency = end_exe - latency_start
    print(f"Trade Latency: {trade_latency:.6f} | Latency: {latency:.6f} seconds")

    if type(account) == CryptoBrokerAccount:
        log = LogMessage.objects.create(
            response_status=response_status,
            alert_message=alert_message,
            response_message=response_message,
            trade=trade,
            latency=latency,
            trade_latency=trade_latency,
            
            content_type=ContentType.objects.get_for_model(CryptoBrokerAccount),
            object_id=account.id
        )
    elif type(account) == ForexBrokerAccount:
        log = LogMessage.objects.create(
            response_status=response_status,
            alert_message=alert_message,
            response_message=response_message,
            latency=latency,
            trade_latency=trade_latency,
            
            content_type=ContentType.objects.get_for_model(ForexBrokerAccount),
            object_id=account.id
        )
    else:
        raise Exception("Account model not supported.")


    return log

def save_new_trade(custom_id, symbol, side, opend_trade, account, strategy_id):
    order_id = opend_trade.get('order_id') 
    # symbol = opend_trade.get('symbol')
    volume = opend_trade.get('qty') or opend_trade.get('volume')
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

def get_previous_trade(custom_id, symbol, side, account, strategy_id, reverse_id):
    t_side = "B" if str.lower(side) == "sell" else "S"

    content_type = ContentType.objects.get_for_model(account.__class__)

    trade = TradeDetails.objects.filter(
        custom_id__contains=f"R{reverse_id}",
        symbol=symbol,
        side=t_side,
        status__in=["O", "P"],
        strategy_id=strategy_id,
        content_type=content_type,
        object_id=account.id
    )

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
    t_side = "B" if str.upper(side) == "BUY" else "S"

    content_type = ContentType.objects.get_for_model(account.__class__)
    with transaction.atomic():
        trade = TradeDetails.objects.select_for_update().filter(
            custom_id=custom_id,
            symbol=symbol,
            side=t_side,
            status__in=["O", "P"],
            strategy_id=strategy_id,
            content_type=content_type,
            object_id=account.id
        ).last()

    return trade

def update_trade_after_close(trade, closed_volume, closed_trade):

    closed_volume = closed_trade.get('qty', closed_volume)
    price = closed_trade.get('price', 0)
    closed_order_id = closed_trade.get('closed_order_id', '')

    closed_trade_details = closed_trade.get('trade_details', None) or closed_trade.get('closed_trade_details', None)

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