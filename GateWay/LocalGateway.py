# -*-coding:utf-8-*-
# @Time:   2021/2/1 14:28
# @Author: FC
# @Email:  18817289038@163.com

import os
import traceback
import pandas as pd
import datetime as dt
from typing import Tuple, Any
from utility import msgPrint

from object import BarData, ApiData
from constant import (
    KeyName as KN,
    Exchange
)

depthPath = r'Y:\十档'
callPath = r'Y:\集合竞价'
tradePath = r'Y:\逐笔全息'

exchangeM = {"深圳": "SZSE",
             "上海": "SSE",
             "SH": "SSE",
             "SZ": "SZSE"}


class LocalGateway(object):

    def __init__(self):
        self.stockApi = StockDataAPI()
        self.indexApi = IndexDataAPI()

        self.apiMapping = {"STOCK": self.stockApi,
                           "INDEX": self.indexApi}

    def load_data(self,
                  data_type: str,
                  symbol: str,
                  date: str,
                  data_name: str = "CALL") -> ApiData:
        """

        Parameters
        ----------
        data_type : 数据类型
        symbol : 股票ID
        date : 时间
        data_name :

        Returns
        -------

        """
        dataDf = self.apiMapping[data_type].load_data(symbol, date, data_name)
        return dataDf


class StockDataAPI(object):
    """
    股票代码要放在最后一位
    """

    def __init__(self):
        self.dataMapping = {
            "DEPTH": {
                "Path": os.path.join(depthPath, 'Stk_Tick10_{year}{month}\\{date_new}\\{exchange}{stock_num}.csv'),
                "Name": "十档",
                "Api": self.query_depth,
                "Process": self.process_depth,
                "Special": self.special_depth},
            "TRADE": {
                "Path": os.path.join(tradePath, '{year}\\{date}\\{stock_num}.csv'),
                "Name": "逐笔全息",
                "Api": self.query_trade,
                "Process": self.process_trade,
                "Special": self.special_trade},
            "CALL": {
                "Path": os.path.join(callPath, '{year}{month}\\{date_new}\\{exchange}{stock_num}_{date_new}.csv'),
                "Name": "集合竞价",
                "Api": self.query_call,
                "Process": self.process_call,
                "Special": self.special_call},
        }

    # load data
    def load_data(self, symbol: str, date: str, data_name: str = 'DEPTH') -> ApiData:
        dataElement = self.dataMapping[data_name]
        try:
            date, stock_id, stock_num, year, month, day, stock_num, exchange, date_new = self.str_split(
                date + '_' + symbol)
            file_path = dataElement['Path'].format(date=date,
                                                   year=year,
                                                   month=month,
                                                   date_new=date_new,
                                                   exchange=exchange.lower(),
                                                   stock_num=stock_num)

            dataHFD = dataElement['Api'](file_path, symbol, date)

            res = ApiData(
                symbol=symbol,
                process=dataElement['Process'],
                data=dataHFD.to_dict('index'),
                open_price=dataElement['Special'](dataHFD, 'open')
            )
        except Exception as e:
            res = ApiData(
                symbol=symbol,
                process=dataElement['Process']
            )
            # msgPrint(f"Load data error, symbol: {symbol}, date: {date}, dataName: {data_name}, error: {e}")
        return res

    # get data
    def query_depth(self, path: str, symbol: str, date: str, **kwargs) -> pd.DataFrame:
        res = pd.read_csv(path, encoding='GBK').drop_duplicates(subset=['时间', '代码'])
        res = res.set_index(['时间', '代码'], drop=False)
        return res

    def query_trade(self, path: str, symbol: str, date: str, **kwargs) -> pd.DataFrame:
        res = pd.read_csv(path, encoding='GBK').drop_duplicates(subset=['TranID', 'Time'])
        res = res.assign(**{"symbol": symbol[:-3],
                            "Mkt": symbol[-2:],
                            "date": date})
        res = res.set_index(['TranID', 'date', 'Time', 'symbol'], drop=False)
        return res

    def query_call(self, path: str, symbol: str, date: str, **kwargs) -> pd.DataFrame:
        res = pd.read_csv(path, encoding='GBK').drop_duplicates(subset=['TradingDay', 'TimeStamp', 'Stkcd'])
        res = res.set_index(['TradingDay', 'TimeStamp', 'Stkcd'], drop=False)
        return res

    # Depth data encapsulation
    def process_depth(self, data, **kwargs) -> BarData:
        bar = BarData(
            symbol=f"{data['代码']:>06}",
            exchange=Exchange[exchangeM[data['市场']]],
            datetime=dt.datetime.strptime(data['时间'], "%Y-%m-%d %H:%M:%S"),
            time=data['时间'].split(" ")[-1],

            volume=data['总量'],  # 累积，暂且替代
            amount=data['总金额'],
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
            raw=data
        )
        return bar

    # Trade data encapsulation
    def process_trade(self, data, **kwargs) -> BarData:
        bar = BarData(
            symbol=f"{data['symbol']:>06}",
            exchange=Exchange[exchangeM[data['Mkt'].upper()]],
            datetime=dt.datetime.strptime(str(data['date']) + str(data['Time']), "%Y-%m-%d%H:%M:%S"),
            time=data['Time'],

            volume=data['Volume'],
            open_price=data['Price'],
            low_price=data['Price'],
            high_price=data['Price'],
            close_price=data['Price'],

            order_type=data['Type'],
            buy_order_price=data['BuyOrderPrice'],
            sale_order_price=data['SaleOrderPrice'],

            buy_order_volume=data['BuyOrderVolume'],
            sale_order_volume=data['BuyOrderVolume'],

            raw=data
        )
        return bar

    # Call data encapsulation
    def process_call(self, data, **kwargs) -> BarData:
        bar = BarData(
            symbol=f"{data['Stkcd']:>06}",
            exchange=Exchange[exchangeM[data['Mkt'].upper()]],
            datetime=dt.datetime.strptime(str(data['TradingDay']) + str(data['TimeStamp']), "%Y%m%d%H%M%S"),
            time=dt.datetime.strftime(dt.datetime.strptime(str(data['TimeStamp']), "%H%M%S"), "%H:%M:%S"),

            volume=data['Volume'],
            open_price=data['LastPrice'],
            low_price=data['LowPrice'],
            high_price=data['HighPrice'],
            close_price=data['LastPrice'],
            preClose_price=data['PreClosePrice'],

            ask_price_1=data['AskPrice1'],
            ask_price_2=data['AskPrice2'],
            ask_price_3=data['AskPrice3'],
            ask_price_4=data['AskPrice4'],
            ask_price_5=data['AskPrice5'],

            ask_volume_1=data['AskQty1'],
            ask_volume_2=data['AskQty2'],
            ask_volume_3=data['AskQty3'],
            ask_volume_4=data['AskQty4'],
            ask_volume_5=data['AskQty5'],

            bid_price_1=data['BidPrice1'],
            bid_price_2=data['BidPrice2'],
            bid_price_3=data['BidPrice3'],
            bid_price_4=data['BidPrice4'],
            bid_price_5=data['BidPrice5'],

            bid_volume_1=data['BidQty1'],
            bid_volume_2=data['BidQty2'],
            bid_volume_3=data['BidQty3'],
            bid_volume_4=data['BidQty4'],
            bid_volume_5=data['BidQty5'],
            raw=data
        )
        return bar

    # Depth
    def special_depth(self, data: pd.DataFrame, para: str) -> Any:
        """
        默认数据不存在缺失，股票数据第一个最新价为开盘价 TODO
        Parameters
        ----------
        data :
        para :

        Returns
        -------

        """
        if para == 'open':
            return data['最新价'][0]

    # Trade
    def special_trade(self, data: pd.DataFrame, para: str) -> Any:
        if para == 'open':
            return data['Price'][0]

    # Call
    def special_call(self, data: pd.DataFrame, para: str) -> Any:
        if para == 'open':
            return data['LastPrice'][-1]

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
dataMapping = {
    "DEPTH": {"Path": os.path.join(depthPath, 'Stk_Tick10_{year}{month}\\{date_new}\\{exchange}{stock_num}.csv'),
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
