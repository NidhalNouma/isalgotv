from typing import TypedDict, Any, NotRequired
from datetime import datetime
from typing import List

class ExchangeInfo(TypedDict):
    symbol: str
    base_asset: str
    quote_asset: str
    base_decimals: str
    quote_decimals: str
    contract_val: NotRequired[float]

class AssetBalance(TypedDict):
    available: float
    locked: float

class AccountBalance(TypedDict):
    __root__: dict[str, AssetBalance]

class OpenTrade(TypedDict):
    message: str
    order_id: str
    closed_order_id: NotRequired[str]
    symbol: str
    side: str
    qty: str|float
    price: str|float
    time: datetime
    fees: str
    currency: str
    trade_details: NotRequired[Any]

class CloseTrade(TypedDict):
    message: str
    order_id: str
    closed_order_id: NotRequired[str]
    qty: str|float
    symbol: NotRequired[str]
    side: NotRequired[str]
    price: NotRequired[str|float]
    time: NotRequired[datetime]
    fees: NotRequired[str]

    trade_details: NotRequired[Any]

class OrderInfo(TypedDict):
    symbol: str
    order_id: str
    volume: str
    side: str
    time: datetime 
    price: str
    fees: str
    profit: NotRequired[str]
    currency: NotRequired[str]
    additional_info: NotRequired[Any]

class TradeDetails(TypedDict):
    order_id: str
    symbol: str
    volume: str
    side: str
    open_price: str
    close_price: str
    open_time: datetime 
    close_time: datetime 
    fees: str
    profit: str
    currency: NotRequired[str]
    additional_info: NotRequired[Any]