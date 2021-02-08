# -*-coding:utf-8-*-
# @Time:   2021/2/1 9:01
# @Author: FC
# @Email:  18817289038@163.com

import sys
import numpy as np
import datetime as dt
from object import BarData
from decimal import Decimal
from constant import Interval
from typing import Callable, Union, Optional, Dict, List

askVols = [f"ask_volume_{i}" for i in range(1, 6)]
bidVols = [f"bid_volume_{i}" for i in range(1, 6)]


class BarGenerator:

    def __init__(
            self,
            on_bar: Callable,
            window: int = 0,
            on_window_bar: Callable = None,
            interval: Interval = Interval.MINUTE
    ):
        """Constructor"""
        self.bar: BarData = None
        self.on_bar: Callable = on_bar

        self.interval: Interval = interval
        self.interval_count: int = 0

        self.window: int = window
        self.window_bar: BarData = None
        self.on_window_bar: Callable = on_window_bar

        self.last_tick: TickData = None
        self.last_bar: BarData = None

    def update_tick(self, bar: BarData) -> None:
        """
        Update new tick data into generator.
        """
        new_minute = False

        # Filter tick data with 0 last price

        if not bar.last_price:
            return

        # Filter tick data with less intraday trading volume (i.e. older timestamp)
        if self.last_tick and bar.volume and bar.volume < self.last_tick.volume:
            return

        if not self.bar:
            new_minute = True
        elif (self.bar.datetime.minute != bar.datetime.minute) or (self.bar.datetime.hour != bar.datetime.hour):
            self.bar.datetime = self.bar.datetime.replace(second=0, microsecond=0)
            self.on_bar(self.bar)

            new_minute = True

        if new_minute:
            self.bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                interval=Interval.MINUTE,
                datetime=bar.datetime,
                time=dt.strptime(bar.datetime, "%H:%M:%S"),
                open_price=bar.last_price,
                high_price=bar.last_price,
                low_price=bar.last_price,
                close_price=bar.last_price,
            )
        else:
            self.bar.high_price = max(self.bar.high_price, bar.last_price)
            self.bar.low_price = min(self.bar.low_price, bar.last_price)
            self.bar.close_price = bar.last_price
            self.bar.datetime = bar.datetime

        if self.last_tick:
            volume_change = bar.volume - self.last_tick.volume
            self.bar.volume += max(volume_change, 0)

        self.last_tick = bar

    # def update_bar(self, bar: BarData) -> None:
    #     """
    #     Update 1 minute bar into generator
    #     """
    #     # If not inited, creaate window bar object
    #     if not self.window_bar:
    #         # Generate timestamp for bar data
    #         if self.interval == Interval.MINUTE:
    #             dt = bar.datetime.replace(second=0, microsecond=0)
    #         else:
    #             dt = bar.datetime.replace(minute=0, second=0, microsecond=0)
    #
    #         self.window_bar = BarData(
    #             symbol=bar.symbol,
    #             exchange=bar.exchange,
    #             datetime=dt,
    #             time=dt.strptime(bar.datetime, "%H:%M:%S"),
    #             open_price=bar.open_price,
    #             high_price=bar.high_price,
    #             low_price=bar.low_price
    #         )
    #     # Otherwise, update high/low price into window bar
    #     else:
    #         self.window_bar.high_price = max(
    #             self.window_bar.high_price, bar.high_price)
    #         self.window_bar.low_price = min(
    #             self.window_bar.low_price, bar.low_price)
    #
    #     # Update close price/volume into window bar
    #     self.window_bar.close_price = bar.close_price
    #     self.window_bar.volume += int(bar.volume)
    #     self.window_bar.open_interest = bar.open_interest
    #
    #     # Check if window bar completed
    #     finished = False
    #
    #     if self.interval == Interval.MINUTE:
    #         # x-minute bar
    #         if not (bar.datetime.minute + 1) % self.window:
    #             finished = True
    #     elif self.interval == Interval.HOUR:
    #         if self.last_bar and bar.datetime.hour != self.last_bar.datetime.hour:
    #             # 1-hour bar
    #             if self.window == 1:
    #                 finished = True
    #             # x-hour bar
    #             else:
    #                 self.interval_count += 1
    #
    #                 if not self.interval_count % self.window:
    #                     finished = True
    #                     self.interval_count = 0
    #
    #     if finished:
    #         self.on_window_bar(self.window_bar)
    #         self.window_bar = None
    #
    #     # Cache last bar object
    #     self.last_bar = bar


# K line manager
class ArrayManager(object):
    """
    For:
    1. time series container of bar data
    2. calculating technical indicator value
    """

    indicators: Dict[str, np.array] = {}

    def __init__(self, size: int = 100):
        """Constructor"""
        self.count: int = 0
        self.size: int = size
        self.inited: bool = False

        self.open_array: np.ndarray = np.zeros(size)
        self.high_array: np.ndarray = np.zeros(size)
        self.low_array: np.ndarray = np.zeros(size)
        self.close_array: np.ndarray = np.zeros(size)
        self.volume_array: np.ndarray = np.zeros(size)

        for i in range(1, 6):
            for name in ['ask_price', 'bid_price', 'ask_volume', 'bid_volume']:
                setattr(self, f'{name}_{i}', np.zeros(size))

    def update_bar(self, bar: BarData) -> None:
        """
        Update new bar data into array manager.
        """
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True

        self.open_array[:-1] = self.open_array[1:]
        self.high_array[:-1] = self.high_array[1:]
        self.low_array[:-1] = self.low_array[1:]
        self.close_array[:-1] = self.close_array[1:]
        self.volume_array[:-1] = self.volume_array[1:]

        self.open_array[-1] = bar.open_price
        self.high_array[-1] = bar.high_price
        self.low_array[-1] = bar.low_price
        self.close_array[-1] = bar.close_price
        self.volume_array[-1] = bar.volume

        for i in range(1, 6):
            for name in ['ask_price', 'bid_price', 'ask_volume', 'bid_volume']:
                att = getattr(self, f'{name}_{i}')
                att[:-1] = att[1:]
                att[-1] = getattr(bar, f'{name}_{i}')

    def update_ind(self, ind_name: List[str]):
        for ind_ in ind_name:
            ind_array = self.indicators.get(ind_, None)
            if ind_array is None:
                self.indicators[ind_] = np.array([np.nan] * self.size)
                ind_array = self.indicators[ind_]
            else:
                ind_array[:-1] = ind_array[1:]

            ind_array[-1] = getattr(self, ind_)()
            self.indicators[ind_] = ind_array

    @property
    def open(self) -> np.ndarray:
        """
        Get open price time series.
        """
        return self.open_array

    @property
    def high(self) -> np.ndarray:
        """
        Get high price time series.
        """
        return self.high_array

    @property
    def low(self) -> np.ndarray:
        """
        Get low price time series.
        """
        return self.low_array

    @property
    def close(self) -> np.ndarray:
        """
        Get close price time series.
        """
        return self.close_array

    @property
    def volume(self) -> np.ndarray:
        """
        Get trading volume time series.
        """
        return self.volume_array

    def VOL_A(self) -> float:
        """
        Time-weighted ask order volume
        :return:
        """
        return np.dot([getattr(self, name)[-1] for name in askVols], time_weight(len(askVols)))

    def VOL_B(self) -> float:
        """
        Time-weighted bid order volume
        :return:
        :rtype:
        """
        return np.dot([getattr(self, name)[-1] for name in bidVols], time_weight(len(bidVols)))


def msgPrint(msg):
    """
    Output message of backtesting engine.
    """
    print(f"{dt.datetime.now()}\t{msg}")


def round_to(value: float, target: float) -> float:
    """
    Round price to price tick value.
    """
    value = Decimal(str(value))
    target = Decimal(str(target))
    rounded = float(int(round(value / target)) * target)
    return rounded


# 时间加权
def time_weight(n: int = 5):
    W_sum = sum(i for i in range(1, n + 1))
    W = sorted([i / W_sum for i in range(1, n + 1)], reverse=True)
    return W
