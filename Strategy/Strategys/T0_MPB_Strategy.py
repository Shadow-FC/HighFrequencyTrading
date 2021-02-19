# -*-coding:utf-8-*-
# @Time:   2021/2/1 9:00
# @Author: FC
# @Email:  18817289038@163.com

import numpy as np
import datetime as dt
from typing import Dict
from constant import Interval, Direction
from Strategy.template import StrategyTemplate
from utility import ArrayManager, BarGenerator
from object import (BarData, TradeData, OrderData)


class T0MPBStrategy(StrategyTemplate):

    pos_all = {}  # Number of tradable lots
    pos_remain = {}

    def __init__(self, engine, strategy_name, vt_symbols, setting):
        """"""
        super().__init__(engine, strategy_name, vt_symbols, setting)

        # self.bgs: Dict[str, BarGenerator] = {}
        self.ams: Dict[str, ArrayManager] = {}
        self.test = 0
        for vt_symbol in self.vt_symbols:
            # self.bgs[vt_symbol] = BarGenerator(self.on_bar, interval=Interval.TICK)
            self.ams[vt_symbol] = ArrayManager(size=2)

    def on_init(self):
        """
        Callback when strategy is inited.
        """

        self.pos_all = self.pos.copy()
        self.pos_remain = self.pos.copy()

        self.load_bar(0, callback=self.on_bar, processData=self.on_bar)

    def on_bar(self, bar: BarData):
        """
        Callback of new tick data update.
        """
        self.test += 1
        if self.inited and '09:30:00' <= bar.time <= '14:56:00':  # TODO 时间条件 + 仓位条件 + 风控，收盘前必须平仓
            self.ams[bar.vt_symbol].update_bar(bar)

            self.ams[bar.vt_symbol].update_ind(['VOL_A', 'VOL_B'])
            self.on_OIR(bar)

    # 订单失衡因子
    def on_OIR(self, bar: BarData):

        id_ = bar.vt_symbol
        if self.pos_remain[id_] != 0 or self.pos[id_] != self.pos_all[id_]:  # 存在可T量同时或头寸未回填满，则进行交易
            # print(f"剩余：{self.pos_remain[id_]}, 实际：{self.pos[id_]}")
            VOL_A = self.ams[id_].indicators['VOL_A']
            VOL_B = self.ams[id_].indicators['VOL_B']
            ask_price_1 = self.ams[id_].ask_price_1
            bid_price_1 = self.ams[id_].bid_price_1

            if len(VOL_A[~np.isnan(VOL_A)]) == 2:

                # delta volume Ask
                if ask_price_1[-1] < ask_price_1[-2]:
                    delta_V_A = VOL_A[-1]
                elif ask_price_1[-1] == ask_price_1[-2]:
                    delta_V_A = VOL_A[-1] - VOL_A[-2]
                else:
                    delta_V_A = 0

                # delta volume Bid
                if bid_price_1[-1] < bid_price_1[-2]:
                    delta_V_B = 0
                elif bid_price_1[-1] == bid_price_1[-2]:
                    delta_V_B = VOL_B[-1] - VOL_B[-2]
                else:
                    delta_V_B = VOL_B[-1]

                if delta_V_B + delta_V_A != 0:
                    OIR = (delta_V_B - delta_V_A) / (delta_V_B + delta_V_A)

                    if OIR > 0.5 and self.pos[id_] != self.pos_all[id_]:
                        self.buy(bar.symbol, bar.exchange, ask_price_1[-1],
                                 min(bar.ask_volume_1, self.pos_all[id_] - self.pos[id_]))

                    if OIR < - 0.5 and self.pos_remain[id_] != 0:
                        self.sell(bar.symbol, bar.exchange, bid_price_1[-1],
                                  min(bar.bid_volume_1, self.pos_remain[id_]))
        # if ('09:30:00' < bar.time < '14:57:00') and bar.symbol != '000002':
        #     if bar.open_price > 12.7 and self.pos_remain[bar.vt_symbol] > 0:
        #         self.sell(bar.symbol, bar.exchange, 12.7,
        #                   min(bar.bid_volume_1, self.pos_remain[bar.vt_symbol]))
        #
        #     if bar.open_price < 12.65 and \
        #             self.pos_remain[bar.vt_symbol] < self.pos_all[bar.vt_symbol] and \
        #             self.pos[bar.vt_symbol] < self.pos_all[bar.vt_symbol]:
        #         self.buy(bar.symbol, bar.exchange, 12.65,
        #                  min(bar.ask_volume_1, self.pos_all[bar.vt_symbol] - self.pos[bar.vt_symbol]))

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.direction == Direction.SHORT:
            self.pos_remain[trade.vt_symbol] -= trade.volume

    def on_position(self, position):
        pass
