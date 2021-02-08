# -*-coding:utf-8-*-
# @Time:   2021/2/1 8:53
# @Author: FC
# @Email:  18817289038@163.com

import time
import traceback
import numpy as np
import pandas as pd
import datetime as dt
from functools import reduce
from collections import defaultdict
from typing import Callable, List, Dict, Union

from utility import msgPrint, round_to
from constant import Direction, Exchange, Status
from GateWay.LocalGateway import LocalGateway, load_data
from object import BarData, TradeData, OrderData, EncapsulationData

exchangeM = {"深圳": "SZSE",
             "上海": "SSE"}


class T0BackTestingEngine:
    """"""
    start_time: dt.datetime = dt.datetime(2020, 12, 31, 9, 15)

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

        self.limit_order_count: int = 0
        self.limit_orders: Dict[str, OrderData] = {}
        self.active_limit_orders: Dict[str, OrderData] = {}

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

    # def load_data(self):
    #     # msgPrint("开始加载历史数据")
    #
    #     self.history_data.clear()  # Clear previously loaded history data
    #
    #     dataNum = 0
    #     for symbol in self.vt_symbols:
    #         data = load_data(symbol, self.dateD, 'DEPTH')  # 参数： 读取数据类型
    #         self.history_data.append(data)
    #         dataNum += data.shape[0]
    #
    #     msgPrint(f"历史数据加载完成，symbol num: {len(self.vt_symbols)}, data num：{dataNum}")
    #
    # def run_backtesting(self):
    #     """"""
    #
    #     self.load_data()
    #
    #     # init strategy
    #     self.strategy.on_init()
    #
    #     # Use the first minutes of history data for initializing strategy
    #     dataInput = pd.concat(self.history_data)
    #     if dataInput.empty:
    #         return pd.DataFrame()
    #
    #     dataInput = dataInput.sort_values(by='时间')  # TODO 如果数据只精确到秒，会出问题
    #     dateInit = (self.start_time + dt.timedelta(minutes=self.minutes)).strftime("%H:%M:%S")
    #     dataInit = dataInput[dataInput['时间'] <= dateInit]
    #
    #     for ix, data in dataInit.iterrows():
    #
    #         try:
    #             bar = BarData(
    #                 symbol=f"{data['代码']:>06}",
    #                 exchange=Exchange[exchangeM[data['市场']]],
    #                 interval=self.interval,
    #                 datetime=dt.datetime.strptime(data['时间'], "%Y-%m-%d %H:%M:%S"),
    #                 time=data['时间'].split(" ")[-1],
    #
    #                 volume=data['总量'],  # 累积，暂且替代
    #                 open_price=data['最新价'],
    #                 low_price=data['最新价'],
    #                 high_price=data['最新价'],
    #                 close_price=data['最新价'],
    #
    #                 ask_price_1=data['挂卖价1'],
    #                 ask_price_2=data['挂卖价2'],
    #                 ask_price_3=data['挂卖价3'],
    #                 ask_price_4=data['挂卖价4'],
    #                 ask_price_5=data['挂卖价5'],
    #
    #                 ask_volume_1=data['挂卖量1'],
    #                 ask_volume_2=data['挂卖量2'],
    #                 ask_volume_3=data['挂卖量3'],
    #                 ask_volume_4=data['挂卖量4'],
    #                 ask_volume_5=data['挂卖量5'],
    #
    #                 bid_price_1=data['挂买价1'],
    #                 bid_price_2=data['挂买价2'],
    #                 bid_price_3=data['挂买价3'],
    #                 bid_price_4=data['挂买价4'],
    #                 bid_price_5=data['挂买价5'],
    #
    #                 bid_volume_1=data['挂买量1'],
    #                 bid_volume_2=data['挂买量2'],
    #                 bid_volume_3=data['挂买量3'],
    #                 bid_volume_4=data['挂买量4'],
    #                 bid_volume_5=data['挂买量5'],
    #                 test=data
    #             )
    #             self.callback(bar)
    #         except Exception:
    #             msgPrint("触发异常，回测终止")
    #             msgPrint(traceback.format_exc())
    #             return
    #
    #     self.strategy.inited = True
    #
    #     # Use the rest of history data for running backtesting
    #     dataPlayback = dataInput[dataInput['时间'] > dateInit]
    #
    #     for ix, data in dataPlayback.iterrows():
    #         try:
    #             bar = BarData(
    #                 symbol=f"{data['代码']:>06}",
    #                 exchange=Exchange[exchangeM[data['市场']]],
    #                 interval=self.interval,
    #                 datetime=dt.datetime.strptime(data['时间'], "%Y-%m-%d %H:%M:%S"),
    #                 time=data['时间'].split(" ")[-1],
    #
    #                 volume=data['总量'],  # 累积，暂且替代
    #                 open_price=data['最新价'],
    #                 low_price=data['最新价'],
    #                 high_price=data['最新价'],
    #                 close_price=data['最新价'],
    #
    #                 ask_price_1=data['挂卖价1'],
    #                 ask_price_2=data['挂卖价2'],
    #                 ask_price_3=data['挂卖价3'],
    #                 ask_price_4=data['挂卖价4'],
    #                 ask_price_5=data['挂卖价5'],
    #
    #                 ask_volume_1=data['挂卖量1'],
    #                 ask_volume_2=data['挂卖量2'],
    #                 ask_volume_3=data['挂卖量3'],
    #                 ask_volume_4=data['挂卖量4'],
    #                 ask_volume_5=data['挂卖量5'],
    #
    #                 bid_price_1=data['挂买价1'],
    #                 bid_price_2=data['挂买价2'],
    #                 bid_price_3=data['挂买价3'],
    #                 bid_price_4=data['挂买价4'],
    #                 bid_price_5=data['挂买价5'],
    #
    #                 bid_volume_1=data['挂买量1'],
    #                 bid_volume_2=data['挂买量2'],
    #                 bid_volume_3=data['挂买量3'],
    #                 bid_volume_4=data['挂买量4'],
    #                 bid_volume_5=data['挂买量5'],
    #                 test=data
    #             )
    #             self.new_bar(bar)
    #         except Exception:
    #             msgPrint("触发异常，回测终止")
    #             msgPrint(traceback.format_exc())
    #             return
    #
    #     res = self.calculate_result()
    #
    #     return res

    # load data for back to the test
    def load_data(self):
        """"""
        dataNum = 0
        for symbol in self.vt_symbols:
            dataClass = self.database.load_data('stock', symbol, self.dateD, 'DEPTH')  # 参数： 读取数据类型
            self.history_data.data.update(dataClass.data)
            self.history_data.process[str(symbol.split('.')[0])] = dataClass.process
            dataNum += len(dataClass.data.keys())
        self.history_data.generate_order()

        msgPrint(f"Date: {self.dateD}, Symbol: {self.vt_symbols[0]}, data num：{dataNum}")

    # Begin to test
    def run_backtesting(self) -> Dict[str, pd.DataFrame]:
        """"""

        self.load_data()

        self.capital = 526

        # init strategy  TODO
        self.strategy.on_init()

        iterIndex = self.history_data.order

        self.strategy.inited = True

        for index_ in iterIndex:
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
        self.cross_limit_order(bar)
        self.onBar(bar)

    def cross_limit_order(self, bar: BarData):
        """
        Cross limit order with last bar data.
        价格低于目标价，则买进，即优价成交
        """

        long_cross_price = bar.low_price
        short_cross_price = bar.high_price
        long_best_price = bar.open_price
        short_best_price = bar.open_price

        for order in list(self.active_limit_orders.values()):
            if order.symbol == bar.symbol:
                # Push order update with status "not traded" (pending).
                if order.status == Status.SUBMITTING:
                    order.status = Status.NOTTRADED
                    self.strategy.on_order(order)

                # Check whether limit orders can be filled.
                long_cross = (order.direction == Direction.LONG and order.price >= long_cross_price > 0)

                short_cross = (
                        order.direction == Direction.SHORT and order.price <= short_cross_price and short_cross_price > 0)

                if not long_cross and not short_cross:
                    continue

                # Push order update with status "all traded" (filled).
                order.traded = order.volume
                order.status = Status.ALLTRADED
                self.strategy.on_order(order)

                self.active_limit_orders.pop(order.vt_order_id)

                # Push trade update
                self.trade_count += 1

                # Assuming a complete transaction
                if long_cross:
                    trade_price = min(order.price, long_best_price)
                    pos_change = order.volume
                else:
                    trade_price = max(order.price, short_best_price)
                    pos_change = -order.volume

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
    ) -> List[str]:
        """"""
        price = round_to(price, self.price_tick)
        self.limit_order_count += 1

        order = OrderData(
            symbol=symbol,
            exchange=exchange,
            order_id=str(self.limit_order_count),
            direction=direction,
            price=price,
            volume=volume,
            status=Status.SUBMITTING,
            datetime=self.datetime
        )

        self.active_limit_orders[order.vt_order_id] = order
        self.limit_orders[order.vt_order_id] = order

        return [order.vt_order_id]

    def cancel_order(self, vt_order_id: str):
        """
        Cancel order by vt_order_id.
        """
        if vt_order_id not in self.active_limit_orders:
            return
        order = self.active_limit_orders.pop(vt_order_id)

        order.status = Status.CANCELLED
        self.strategy.on_order(order)

    def cancel_all(self):
        """
        Cancel all orders.
        """
        vt_order_ids = list(self.active_limit_orders.keys())
        for vt_order_id in vt_order_ids:
            self.cancel_order(vt_order_id)

    def calculate_result(self) -> Dict[str, pd.DataFrame]:
        """"""
        # Calculate daily result by iteration.
        results = defaultdict(list)
        for symbol, daily_result in self.daily_results.items():

            daily_result.calculate_pnl(self.size, self.rate, self.slippage)
            for key, value in daily_result.__dict__.items():
                if key == 'trades':
                    continue
                results[key].append(value)

            self.daily_df[symbol] = pd.DataFrame(results).set_index('date')

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

        self.trades = []  # 交易记录

        self.end_pos = 0  # 剩余头寸
        self.trade_long = 0  # long次数
        self.trade_short = 0  # short次数

        self.turnover = 0  # 累积交易金额
        self.commission = 0  # 佣金

        self.slippage = 0  # 滑点

        self.account = 0  # 账户金额

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

        # Trading pnl is the pnl from new trade during the day TODO 有问题
        self.end_pos = self.start_pos
        self.account = self.capital

        for trade in self.trades:
            if trade.direction == Direction.LONG:
                pos_change = trade.volume
                self.trade_long += 1
            else:
                pos_change = -trade.volume
                self.trade_short += 1

            self.end_pos += pos_change
            turnover = trade.volume * size * trade.price
            self.account -= pos_change * trade.price * size
            self.slippage += trade.volume * size * slippage

            self.turnover += turnover
            self.commission += turnover * rate

