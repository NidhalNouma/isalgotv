from django.contrib.contenttypes.models import ContentType

from decimal import Decimal
from django.utils import timezone

from ..models import *

from .brokers.binance import BinanceClient
from .brokers.binance_us import BinanceUSClient
from .brokers.bitget import BitgetClient
from .brokers.bybit import BybitClient
from .brokers.mexc import MexcClient
from .brokers.crypto import CryptoComClient
from .brokers.bingx import BingxClient

from .brokers.trade_locker import check_tradelocker_credentials, open_tradelocker_trade, close_tradelocker_trade, get_tradelocker_trade_data
from .brokers.metatrader import add_metatrader_account, open_metatrader_trade, close_metatrader_trade, get_metatrader_trade_data

def check_crypto_credentials(broker_type, api_key, api_secret, phrase, account_type="S"):
    print("Checking crypto credentials for " + broker_type)
    if broker_type == 'binance':
        return BinanceClient.check_credentials(api_key, api_secret, account_type)
    if broker_type == 'binanceus':
        return BinanceUSClient.check_credentials(api_key, api_secret)
    elif broker_type == 'bitget':
        return BitgetClient.check_credentials(api_key, api_secret, phrase, account_type)
    elif broker_type == 'bybit':
        return BybitClient.check_credentials(api_key, api_secret, account_type)
    elif broker_type == 'mexc':
        return MexcClient.check_credentials(api_key, api_secret, account_type)
    elif broker_type == 'crypto':
        return CryptoComClient.check_credentials(api_key, api_secret, account_type)
    elif broker_type == 'bingx':
        return BingxClient.check_credentials(api_key, api_secret, account_type)
    else:
        raise Exception("Unsupported broker type.")

def check_forex_credentials(broker_type, username, password, server, type="D"):
    
    if broker_type == 'tradelocker':
        return check_tradelocker_credentials(username, password, server, type)
    elif broker_type == 'metatrader4':
        return add_metatrader_account(username, username, password, server, "mt4")
    elif broker_type == 'metatrader5':
        return add_metatrader_account(username, username, password, server, "mt5")
    else:
        raise Exception("Unsupported broker type.")

    
def open_trade_by_account(account, symbol, side, volume, custom_id):
    try:
        broker_type = account.broker_type
        if broker_type == 'binance':
            return BinanceClient(account=account).open_trade(symbol, side, volume, custom_id)
        elif broker_type == 'binanceus':
            return BinanceUSClient(account=account).open_trade(symbol, side, volume, custom_id)
        elif broker_type == 'bitget':
            return BitgetClient(account=account).open_trade(symbol, side, volume)
        elif broker_type == 'bybit':
            return BybitClient(account=account).open_trade(symbol, side, volume)
        elif broker_type == 'mexc':
            return MexcClient(account=account).open_trade(symbol, side, volume)
        elif broker_type == 'crypto':
            return CryptoComClient(account=account).open_trade(symbol, side, volume)
        elif broker_type == 'bingx':
            return BingxClient(account=account).open_trade(symbol, side, volume)
        elif broker_type == 'tradelocker':
            return open_tradelocker_trade(account, symbol, side, volume)
        elif broker_type == 'metatrader4' or broker_type == 'metatrader5':
            return open_metatrader_trade(account, side.lower(), symbol, volume)
        else:
            raise Exception("Unsupported broker type.")
    except Exception as e:
        print('open trade error: ', str(e))
        raise e
    
def close_trade_by_account(account, trade_to_close, symbol, side, volume_close):
    try:
        broker_type = account.broker_type
        if broker_type == 'binance':
            return BinanceClient(account=account, current_trade=trade_to_close).close_trade(symbol, side, volume_close)
        elif broker_type == 'binanceus':
            return BinanceUSClient(account=account, current_trade=trade_to_close).close_trade(symbol, side, volume_close)
        elif broker_type == 'bitget':
            return BitgetClient(account=account, current_trade=trade_to_close).close_trade(symbol, side, volume_close)
        elif broker_type == 'bybit':
            return BybitClient(account=account, current_trade=trade_to_close).close_trade(symbol, side, volume_close)
        elif broker_type == 'mexc':
            return MexcClient(account=account, current_trade=trade_to_close).close_trade(symbol, side, volume_close)
        elif broker_type == 'crypto':
            return CryptoComClient(account=account, current_trade=trade_to_close).close_trade(symbol, side, volume_close)
        elif broker_type == 'bingx':
            return BingxClient(account=account, current_trade=trade_to_close).close_trade(symbol, side, volume_close)
        elif broker_type == 'tradelocker':
            return close_tradelocker_trade(account, trade_to_close, volume_close)
        elif broker_type == 'metatrader4' or broker_type == 'metatrader5':
            return close_metatrader_trade(account, trade_to_close, volume_close)
        else:
            raise Exception("Unsupported broker type.")
    except Exception as e:
        print('close trade error: ', str(e))
        raise e

def get_trade_data(account, trade):
    try:
        broker_type = account.broker_type
        if broker_type == 'binance':
            return BinanceClient(account).get_final_trade_details(trade)
        elif broker_type == 'binanceus':
            return BinanceUSClient(account).get_final_trade_details(trade)
        elif broker_type == 'bitget':
            return BitgetClient(account).get_final_trade_details(trade)
        elif broker_type == 'bybit':
            return BybitClient(account).get_final_trade_details(trade)
        elif broker_type == 'mexc':
            return MexcClient(account).get_final_trade_details(trade)
        elif broker_type == 'crypto':
            return CryptoComClient(account).get_final_trade_details(trade)
        elif broker_type == 'tradelocker':
            return get_tradelocker_trade_data(account, trade)
        elif broker_type == 'metatrader4' or broker_type == 'metatrader5':
            return get_metatrader_trade_data(account, trade)
        else:
            raise Exception("Unsupported broker type.")
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

def update_trade_after_close(trade, closed_volume, closed_trade):

    closed_volume = closed_trade.get('qty', closed_volume)
    price = closed_trade.get('price', 0)
    closed_order_id = closed_trade.get('closed_order_id', '')

    closed_trade_details = closed_trade.get('trade_details', None)

    trade.closed_trade_details = closed_trade_details

    trade.exit_price = float(price)
    trade.closed_order_id = closed_order_id
    trade.remaining_volume = float(trade.remaining_volume) - float(closed_volume)
    if float(trade.remaining_volume) <= 0:
        trade.status = 'C'
    else:
        trade.status = 'P'
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