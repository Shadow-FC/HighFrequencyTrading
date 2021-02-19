# -*-coding:utf-8-*-
# @Time:   2021/2/1 8:55
# @Author: FC
# @Email:  18817289038@163.com

import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from constant import Interval, Offset, Direction, Exchange, Status, OrderType
from typing import Any, Callable, Dict, Tuple, List


@dataclass
class BarData:
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str
    datetime: datetime
    time: str
    exchange: Exchange
    interval: Interval = None

    raw: Any = None

    volume: float = 0
    amount: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    preClose_price: float = 0

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0

    order_type: str = None
    buy_order_volume: float = 0
    sale_order_volume: float = 0

    buy_order_price: float = 0
    sale_order_price: float = 0

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderData:
    """
    Order data contains information for tracking lastest status
    of a specific order.
    """

    symbol: str
    order_id: str
    status: Status
    exchange: Exchange
    order_type: OrderType

    direction: Direction = None
    price: float = 0
    volume: float = 0
    traded: float = 0

    datetime: datetime = None

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_order_id = f"{self.vt_symbol}.{self.order_id}"


@dataclass
class TradeData:
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """

    symbol: str
    order_id: str
    trade_id: str
    exchange: Exchange
    direction: Direction = None

    price: float = 0
    volume: float = 0
    # time: str = None
    datetime: datetime = None

    def __post_init__(self):
        self.vt_trader_id = f"{self.symbol}.{self.trade_id}"
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class ApiData:
    symbol: str
    process: Callable = field(default_factory=dict)
    data: Dict[Tuple[str], pd.Series] = field(default_factory=dict)
    open_price: float = 0


@dataclass
class EncapsulationData:

    symbol: str = ''
    order: List[Tuple[str]] = field(default_factory=list)
    process: Dict[str, Callable] = field(default_factory=dict)
    data: Dict[Tuple[str], pd.Series] = field(default_factory=dict)

    def generate_order(self):
        self.order = sorted(self.data.keys())
