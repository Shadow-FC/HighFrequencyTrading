""""""
from abc import ABC
from collections import defaultdict
from typing import Any, Callable, List, Dict

from constant import Interval, Direction, Exchange
from object import BarData, OrderData, TradeData


class StrategyTemplate(ABC):
    """"""

    author = "FC"
    parameters = []
    variables = []

    def __init__(
        self,
        engine: Any,
        strategy_name: str,
        vt_symbols: List[str],
        setting: dict,
    ):
        """"""
        self.engine = engine
        self.strategy_name: str = strategy_name
        self.vt_symbols: List[str] = vt_symbols

        self.inited: bool = False

        self.pos: Dict[str, int] = defaultdict(int)
        self.orders: Dict[str, OrderData] = {}
        self.active_order_ids: Set[str] = set()

        self.variables.insert(0, "inited")
        self.variables.insert(1, "pos")

        self.update_setting(setting)

    def update_setting(self, setting: dict):
        """
        Update strategy parameter with value in setting dict.
        """
        for name in self.parameters + ['pos']:
            if name in setting:
                setattr(self, name, setting[name])

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        pass

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def buy(self, symbol: str, exchange: Exchange, price: float, volume: float):
        """
        Send buy order to open a long position.
        """
        return self.send_order(symbol, exchange, Direction.LONG, price, volume)

    def sell(self, symbol: str, exchange: Exchange, price: float, volume: float):
        """
        Send sell order to close a long position.
        """
        return self.send_order(symbol, exchange, Direction.SHORT, price, volume)

    def send_order(self, symbol: str, exchange: Exchange, direction: Direction, price: float, volume: float):
        """
        Send a new order.
        """
        vt_order_ids = self.engine.send_order(symbol, exchange, direction, price, volume)
        return vt_order_ids

    def cancel_order(self, vt_order_id: str):
        """
        Cancel an existing order.
        """
        self.engine.cancel_order(vt_order_id)

    def cancel_all(self):
        """
        Cancel all orders sent by strategy.
        """
        self.engine.cancel_all(self)

    def load_bar(self,
                 minutes: int,
                 callback: Callable = None,
                 processData: Callable = None):
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback = self.on_bar

        if not processData:
            processData = self.on_bar

        self.engine.load_bar(minutes, callback, processData)
