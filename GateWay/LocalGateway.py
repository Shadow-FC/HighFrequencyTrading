# -*-coding:utf-8-*-
# @Time:   2021/2/1 14:28
# @Author: FC
# @Email:  18817289038@163.com

import os
import pandas as pd
import datetime as dt
from typing import Tuple

from object import BarData, ApiData
from constant import (
    KeyName as KN,
    Exchange
)


depthPath = r'Y:\十档'
callPath = r'B:\集合竞价'
tradePath = r'B:\逐笔全息'

exchangeM = {"深圳": "SZSE",
             "上海": "SSE"}


class LocalGateway(object):

    def __init__(self):
        self.stockApi = StockDataAPI()
        self.indexApi = IndexDataAPI()

        self.apiMapping = {"stock": self.stockApi,
                           "index": self.indexApi}

    def load_data(self,
                  dataType: str,
                  symbol: str,
                  date: str,
                  data_name: str = "CALL"):
        dataDf = self.apiMapping[dataType].load_data(symbol, date, data_name)
        return dataDf


class StockDataAPI(object):

    def __init__(self):
        self.dataMapping = {
            "DEPTH": {"Path": os.path.join(depthPath, 'Stk_Tick10_{year}{month}\\{date_new}\\{exchange}{stock_num}.csv'),
                      "Name": "十档",
                      "File": 'DepthMerge',
                      "process": self.processDepth},
            "TRADE": {"Path": os.path.join(tradePath, '{year}\\{date}\\{stock_num}.csv'),
                      "Name": "逐笔全息",
                      "File": 'TradeMerge',
                      "process": self.processTrade},
            "CALL": {"Path": os.path.join(callPath, '{year}{month}\\{date_new}\\{exchange}{stock_num}_{date_new}.csv'),
                     "Name": "集合竞价",
                     "File": 'CallMerge',
                     "process": self.processCall},
        }

    # load data
    def load_data(self, symbol: str, date: str, data_name: str = 'CALL') -> ApiData:
        dataElement = self.dataMapping[data_name]
        date, stock_id, stock_num, year, month, day, stock_num, exchange, date_new = self.str_split(date + '_' + symbol)
        file_path = dataElement['Path'].format(date=date,
                                               year=year,
                                               month=month,
                                               date_new=date_new,
                                               exchange=exchange.lower(),
                                               stock_num=stock_num)
        try:
            dataHFD = pd.read_csv(file_path, encoding='GBK').drop_duplicates(subset=['时间', '代码']).set_index(['时间', '代码'], drop=False)

            res = ApiData(
                symbol=symbol,
                process=dataElement['process'],
                data=dataHFD.to_dict('index')
            )
        except Exception as e:
            res = ApiData(
                symbol=symbol,
                process=dataElement['process']
            )

        return res

    # Depth data encapsulation
    def processDepth(self, data, **kwargs) -> BarData:
        bar = BarData(
            symbol=f"{data['代码']:>06}",
            exchange=Exchange[exchangeM[data['市场']]],
            datetime=dt.datetime.strptime(data['时间'], "%Y-%m-%d %H:%M:%S"),
            time=data['时间'].split(" ")[-1],

            volume=data['总量'],  # 累积，暂且替代
            open_price=data['最新价'],
            low_price=data['最新价'],
            high_price=data['最新价'],
            close_price=data['最新价'],

            ask_price_1=data['挂卖价1'],
            ask_price_2=data['挂卖价2'],
            ask_price_3=data['挂卖价3'],
            ask_price_4=data['挂卖价4'],
            ask_price_5=data['挂卖价5'],

            ask_volume_1=data['挂卖量1'],
            ask_volume_2=data['挂卖量2'],
            ask_volume_3=data['挂卖量3'],
            ask_volume_4=data['挂卖量4'],
            ask_volume_5=data['挂卖量5'],

            bid_price_1=data['挂买价1'],
            bid_price_2=data['挂买价2'],
            bid_price_3=data['挂买价3'],
            bid_price_4=data['挂买价4'],
            bid_price_5=data['挂买价5'],

            bid_volume_1=data['挂买量1'],
            bid_volume_2=data['挂买量2'],
            bid_volume_3=data['挂买量3'],
            bid_volume_4=data['挂买量4'],
            bid_volume_5=data['挂买量5'],
            test=data
        )
        return bar

    # Trade data encapsulation
    def processTrade(self, data):
        pass

    # Call data encapsulation
    def processCall(self, data):
        pass

    @staticmethod
    def str_split(date_stock: str) -> Tuple:
        date, stock_id = date_stock.split('_')
        year, month, day = date.split('-')
        stock_num, exchange = stock_id.split('.')
        date_new = year + month + day
        return date, stock_id, stock_num, year, month, day, stock_num, exchange.lower(), date_new


class IndexDataAPI(object):
    pass


# 测试用
dataMapping = {"DEPTH": {"Path": os.path.join(depthPath, 'Stk_Tick10_{year}{month}\\{date_new}\\{exchange}{stock_num}.csv'),
                         "Name": "十档",
                         "File": 'DepthMerge'},
               "TRADE": {"Path": os.path.join(tradePath, '{year}\\{date}\\{stock_num}.csv'),
                         "Name": "逐笔全息",
                         "File": 'TradeMerge'},
               "CALL": {"Path": os.path.join(callPath, '{year}{month}\\{date_new}\\{exchange}{stock_num}_{date_new}.csv'),
                        "Name": "集合竞价",
                        "File": 'CallMerge'},
               }


def load_data(symbol: str, date: str, data_name: str = 'CALL'):
    dataElement = dataMapping[data_name]
    date, stock_id, stock_num, year, month, day, stock_num, exchange, date_new = str_split(date + '_' + symbol)
    file_path = dataElement['Path'].format(date=date,
                                           year=year,
                                           month=month,
                                           date_new=date_new,
                                           exchange=exchange.lower(),
                                           stock_num=stock_num)
    try:
        dataHFD = pd.read_csv(file_path, encoding='GBK')
    except Exception as e:
        dataHFD = pd.DataFrame()
    return dataHFD


def str_split(date_stock: str):
        date, stock_id = date_stock.split('_')
        year, month, day = date.split('-')
        stock_num, exchange = stock_id.split('.')
        date_new = year + month + day
        return date, stock_id, stock_num, year, month, day, stock_num, exchange.lower(), date_new


if __name__ == '__main__':
    A = LocalGateway()
