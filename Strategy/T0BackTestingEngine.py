# -*-coding:utf-8-*-
# @Time:   2021/2/1 8:53
# @Author: FC
# @Email:  18817289038@163.com

import time
import logging
import traceback
import numpy as np
import pandas as pd
import datetime as dt
from functools import reduce
from collections import defaultdict
from typing import Callable, List, Dict, Union

from utility import msgPrint, round_to
from constant import Direction, Exchange, Status, OrderType, KeyName as KN
from GateWay.LocalGateway import LocalGateway, load_data
from object import BarData, TradeData, OrderData, EncapsulationData


class T0BackTestingEngine:
    """"""
    start_time: dt.datetime = dt.datetime(2020, 12, 31, 9, 15)

    API_Para = {}

    def __init__(self):
        """"""
        self.database: type = LocalGateway()
        self.vt_symbols: List[str] = [""]  # 股票IDList
        self.dateD: str = None  # 回测时间
        self.rate: float = 0  # 手续费
        self.slippage: float = 0  # 滑点
        self.size: float = 1  # 最小交易股数
        self.price_tick: float = 0  # 最小一跳
        self.capital: float = 1_000_000  # 总资金

        self.strategy = None  # 实例化策略
        self.datetime: str = None  # 时间

        self.minutes: int = 0  # 初始化所需分钟数
        self.callback: Callable = None  # 回调初始化函数
        self.onBar: Callable = None  # 回调策略逻辑函数
        self.history_data: EncapsulationData = EncapsulationData()  # 历史数据容器
        self.dataOrder = None

        self.order_count: int = 0
        self.orders: Dict[str, OrderData] = {}
        self.active_orders: Dict[str, OrderData] = {}

        self.trade_count: int = 0

        self.daily_results: Dict[str, DailyResult] = {}  # 交易数据处理类
        self.daily_df: Dict[str, pd.DataFrame] = {}  # 每日交易结果

    def set_parameters(
            self,
            vt_symbols: List[str],
            dateD: str,
            rate: float,
            slippage: float,
            size: float,
            price_tick: float,
            capital: int = 0
    ):
        """"""
        self.vt_symbols = vt_symbols
        self.rate = rate
        self.slippage = slippage
        self.size = size
        self.price_tick = price_tick
        self.dateD = dateD

        self.capital = capital

    # add strategy and instantiation strategy
    def add_strategy(self, strategy_class: type, setting: dict):
        """"""
        self.strategy = strategy_class(self, strategy_class.__name__, self.vt_symbols, setting)
        self.daily_results = {k: DailyResult(self.dateD, k, setting.get('pos', {}).get(k, 0), self.capital)
                              for k in self.vt_symbols}

    # load data for back to the test
    def load_data(self):
        """"""
        dataNum = 0
        for symbol in self.vt_symbols:
            dataClass = self.database.load_data(symbol=symbol, date=self.dateD, **self.API_Para)  # 参数： 读取数据类型
            self.history_data.data.update(dataClass.data)
            self.history_data.process[str(symbol.split('.')[0])] = dataClass.process
            self.daily_results[symbol].open_price = dataClass.open_price
            dataNum += len(dataClass.data.keys())
        self.history_data.generate_order()

        msgPrint(f"Date: {self.dateD}, Symbol: {self.vt_symbols}, data num：{dataNum}")

    # Begin to test
    def run_backtesting(self) -> Dict[str, pd.DataFrame]:
        """"""

        self.load_data()

        # init strategy  TODO
        self.strategy.on_init()

        self.strategy.inited = True

        for index_ in self.history_data.order:
            try:
                dataSet = self.history_data.data[index_]
                bar = self.history_data.process[str(index_[-1])](dataSet)
                self.new_bar(bar)
            except Exception:
                msgPrint("触发异常，回测终止")
                msgPrint(traceback.format_exc())
                return

        res = self.calculate_result()

        return res

    def new_bar(self, bar: BarData):
        """"""
        self.datetime = bar.datetime

        # limit order
        self.cross_order(bar)
        self.onBar(bar)

    def cross_order(self, bar: BarData):
        """
        Cross order with last bar data.
        if order type == LIMIT:
            价格低于目标价，则买进，即优价成交
        elif orderType == MARKET:
            市场最优价成交(开盘价成交)
        elif orderType == PAPER:
            按照提交价格成交
        else:
            不交易

        默认全部成交
        """

        long_cross_price = bar.low_price
        short_cross_price = bar.high_price
        long_best_price = bar.open_price
        short_best_price = bar.open_price

        for order in list(self.active_orders.values()):
            if order.symbol == bar.symbol:
                # Push order update with status "not traded" (pending).
                if order.status == Status.SUBMITTING:
                    order.status = Status.NOTTRADED
                    self.strategy.on_order(order)

                if order.order_type == OrderType.LIMIT:
                    # Check whether limit orders can be filled.
                    long_cross = (order.direction == Direction.LONG and order.price >= long_cross_price > 0)
                    short_cross = (
                            order.direction == Direction.SHORT and order.price <= short_cross_price and short_cross_price > 0)
                elif order.order_type in (OrderType.PAPER, OrderType.MARKET):
                    # There's gonna be a deal
                    long_cross = order.direction == Direction.LONG
                    short_cross = order.direction == Direction.SHORT
                else:
                    long_cross = short_cross = False

                if not long_cross and not short_cross:
                    continue

                # Push order update with status "all traded" (filled).
                order.traded = order.volume
                order.status = Status.ALLTRADED
                self.strategy.on_order(order)

                self.active_orders.pop(order.vt_order_id)

                # Push trade update
                self.trade_count += 1

                # Assuming a complete transaction
                if order.order_type == OrderType.LIMIT:
                    trade_price = min(order.price, long_best_price) if long_cross else max(order.price, short_best_price)
                elif order.order_type == OrderType.MARKET:
                    trade_price = long_best_price if long_cross else short_best_price
                else:
                    trade_price = order.price

                pos_change = order.volume if long_cross else -order.volume

                trade = TradeData(
                    symbol=order.symbol,
                    order_id=order.order_id,
                    exchange=order.exchange,
                    trade_id=str(self.trade_count),
                    direction=order.direction,
                    price=trade_price,
                    volume=order.volume,
                    datetime=self.datetime,
                )

                self.daily_results[bar.vt_symbol].add_trade(trade)

                self.strategy.pos[bar.vt_symbol] += pos_change
                self.strategy.on_trade(trade)  # Push traded order to strategy

    def load_bar(self, minutes: int, callback: Callable, processData: Callable):
        """"""
        self.minutes = minutes
        self.callback = callback
        self.onBar = processData  # strategy logic function

    def send_order(
            self,
            symbol: str,
            exchange: Exchange,
            direction: Direction,
            price: float,
            volume: float,
            orderType: OrderType
    ) -> List[str]:
        """"""
        price = round_to(price, self.price_tick)
        self.order_count += 1

        order = OrderData(
            symbol=symbol,
            exchange=exchange,
            order_id=str(self.order_count),
            direction=direction,
            order_type=orderType,
            price=price,
            volume=volume,
            status=Status.SUBMITTING,
            datetime=self.datetime
        )

        self.active_orders[order.vt_order_id] = order
        self.orders[order.vt_order_id] = order

        return [order.vt_order_id]

    def cancel_order(self, vt_order_id: str):
        """
        Cancel order by vt_order_id.
        """
        if vt_order_id not in self.active_orders:
            return
        order = self.active_orders.pop(vt_order_id)

        order.status = Status.CANCELLED
        self.strategy.on_order(order)

    def cancel_all(self):
        """
        Cancel all orders.
        """
        vt_order_ids = list(self.active_orders.keys())
        for vt_order_id in vt_order_ids:
            self.cancel_order(vt_order_id)

    def calculate_result(self) -> Dict[str, pd.DataFrame]:
        """"""
        # Calculate daily result by iteration.
        for symbol, daily_result in self.daily_results.items():
            results = defaultdict(list)

            daily_result.calculate_pnl(self.size, self.rate, self.slippage)
            daily_result.switchFormat()
            for key, value in daily_result.__dict__.items():
                if key == 'trades':
                    continue
                results[key].append(value)

            self.daily_df[symbol] = pd.DataFrame(results).set_index(KN.TRADE_DATE.value)

        # Multi-asset consolidation
        self.multi_asset_merger(self.daily_df)

        return self.daily_df

    def multi_asset_merger(self, df_dict: Dict[str, pd.DataFrame]):
        """Merge required fields"""

        if len(self.vt_symbols) != 1:
            self.daily_df['portfolio'] = reduce(lambda x, y: x + y, df_dict.values())
        else:
            self.daily_df['portfolio'] = df_dict[self.vt_symbols[0]]


class DailyResult:
    """
    Daily profit and loss calculation
    """

    def __init__(self,
                 date: dt.date,
                 symbol: str,
                 pos: int,
                 capital: float):
        """"""
        self.symbol = symbol  # ID
        self.date = date  # 交易日期
        self.start_pos = pos  # 起始头寸
        self.capital = capital  # 起始资金

        self.open_price = 0  # 当天开盘价
        self.trades = []  # 交易记录

        self.stock_account = 0
        self.capital_account = 0  # 账户现金资产价值

        self.end_pos = 0  # 剩余头寸
        self.trade_long = 0  # long次数
        self.trade_short = 0  # short次数

        self.turnover = 0  # 累积交易金额
        self.commission = 0  # 佣金

        self.slippage = 0  # 滑点

        self.account = 0  # 初始账户资产价值

    def add_trade(self, trade: TradeData):
        """"""
        self.trades.append(trade)

    def calculate_pnl(
            self,
            size: int,
            rate: float,
            slippage: float
    ):
        """"""

        # Trading pnl is the pnl from new trade during the day
        self.end_pos = self.start_pos
        self.stock_account = self.open_price * self.end_pos * size
        self.capital_account = self.capital

        self.account = self.stock_account + self.capital

        for trade in self.trades:
            if trade.direction == Direction.LONG:
                pos_change = trade.volume
                self.trade_long += 1
            else:
                pos_change = -trade.volume
                self.trade_short += 1

            self.end_pos += pos_change
            self.stock_account = trade.price * self.end_pos * size

            turnover = trade.volume * size * trade.price
            self.capital_account -= pos_change * trade.price * size
            self.slippage += trade.volume * size * slippage

            self.turnover += turnover
            self.commission += turnover * rate

    def switchFormat(self):
        self.start_pos = [{self.symbol: self.start_pos}]
        self.end_pos = [{self.symbol: self.end_pos}]
        self.open_price = [{self.symbol: self.open_price}]
        self.symbol = [self.symbol]


class LogEngine(object):
    pass
