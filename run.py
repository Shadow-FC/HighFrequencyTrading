# -*-coding:utf-8-*-
# @Time:   2021/1/29 18:24
# @Author: FC
# @Email:  18817289038@163.com

import time
import numpy as np
import pandas as pd
from typing import List
from multiprocessing import Pool

from constant import (
    KeyName as KN
)
from StockPool.StockPool import StockPool
from Strategy.Strategys import LoadStrategy
from Strategy.T0BackTestingEngine import T0BackTestingEngine


# TODO 目前没有考虑K先合成，后续补

def Initialization(sample: pd.DataFrame, strategyClass) -> List[T0BackTestingEngine]:
    # 设置参数并加载策略
    engineList = []
    for id_, sampleSub in sample.iterrows():
        engine = T0BackTestingEngine()
        engine.set_parameters(
            vt_symbols=[sampleSub[KN.STOCK_ID.value]],
            dateD=sampleSub[KN.TRADE_DATE.value],
            rate=1.5 / 1000,
            slippage=0,
            size=100,
            price_tick=0.01,
            capital=1_000_000,  # 可以作为参数按个股设置
        )
        engine.add_strategy(strategyClass, {"pos": {sampleSub[KN.STOCK_ID.value]: 10000}})
        engineList.append(engine)
    return engineList


def mp(Engine: List[T0BackTestingEngine]) -> pd.DataFrame:
    # 读取数据并回测
    P = Pool(2)
    processList = []
    start = time.time()
    for engine_ in Engine:
        process = P.apply_async(func=engine_.run_backtesting)
        processList.append(process)
    P.close()
    P.join()
    print(time.time() - start)
    resList = []
    for res_ in processList:
        resList.append(res_.get()['portfolio'])
    res = pd.concat(resList)
    return res


def test(Engine: List[T0BackTestingEngine]) -> pd.DataFrame:
    # 读取数据并回测
    resList = []
    start = time.time()
    T = []
    for engine_ in Engine:
        start = time.time()
        res = engine_.run_backtesting()
        end = time.time() - start
        T.append(end)
        print(f"{end}-{engine_.strategy.test}")

        resList.append(res['portfolio'])

    print(f"测试样本量：{len(T)}，平均耗时：{np.mean(T)}")

    res = pd.concat(resList)
    return res


if __name__ == '__main__':
    S = LoadStrategy()
    # 获取股票池
    SP = StockPool()
    effectSample = SP.StockPoolZD()
    effectSample = effectSample.reset_index().iloc[-20:]
    engineStrategy = Initialization(effectSample, S.classes['T0Strategy'])
    bt_res = test(engineStrategy)
    print('s')
