# -*-coding:utf-8-*-
# @Time:   2021/2/1 8:54
# @Author: FC
# @Email:  18817289038@163.com

from enum import Enum, unique


@unique
class Direction(Enum):
    """
    Direction of order/trade/position.
    """
    LONG = "多"
    SHORT = "空"
    NET = "净"


@unique
class Offset(Enum):
    """
    Offset of order/trade.
    """
    NONE = ""
    OPEN = "开"
    CLOSE = "平"
    CLOSETODAY = "平今"
    CLOSEYESTERDAY = "平昨"


@unique
class Status(Enum):
    """
    Order status.
    """
    SUBMITTING = "提交中"
    NOTTRADED = "未成交"
    PARTTRADED = "部分成交"
    ALLTRADED = "全部成交"
    CANCELLED = "已撤销"
    REJECTED = "拒单"


@unique
class OrderType(Enum):
    """
    Order type.
    """
    LIMIT = "限价"
    MARKET = "市价"
    STOP = "STOP"
    FAK = "FAK"
    FOK = "FOK"
    PAPER = "理论价格"


@unique
class Interval(Enum):
    """
    Interval of bar data.
    """
    MINUTE = "1m"
    HOUR = "1h"
    DAILY = "d"
    WEEKLY = "w"
    TICK = "tick"


@unique
class KeyName(Enum):
    STOCK_ID = 'code'
    TRADE_DATE = 'date'
    TRADE_TIME = 'time'
    LIST_DATE = 'listDate'
    RETURN = 'ret'


class FilePathName(Enum):
    # factor_info = 'Z:\\Database\\'  # 因子信息路径

    Input_data_server = 'Y:\\DataBase'  # 服务端数据
    Input_data_local = 'A:\\DataBase\\SecuritySelectData\\InputData'  # 本地数据

    factor_pool_path = 'A:\\DataBase\\SecuritySelectData\\FactorPool\\'  # 因子池
    factor_inputData = 'A:\\DataBase\\SecuritySelectData\\FactorPool\\Factor_InputData\\'  # 因子计算所需数据
    FactorRawData = "A:\\DataBase\\SecuritySelectData\\FactorPool\\FactorDataSet\\RawDataFundamental\\"  # 未经过处理的因子集
    # FactorDataSet = "A:\\DataBase\\SecuritySelectData\\FactorPool\\FactorDataSet\\"  # 标准因子集(日频)
    FactorDataSet = "D:\\DataBase\\NEW2"  # 标准因子集(日频)
    factor_test_res = "A:\\DataBase\\SecuritySelectData\\FactorPool\\FactorsTestResult\\"  # 因子检验结果保存

    factor_ef = "A:\\DataBase\\SecuritySelectData\\FactorPool\\FactorEffective\\"  # 筛选有效因子集
    factor_comp = "A:\\DataBase\\SecuritySelectData\\FactorPool\\FactorEffective\\FactorComp\\"  # 复合因子数据集

    Trade_Date = 'Y:\\DataBase'  # 交易日
    List_Date = 'A:\\DataBase\\ListDate'  # 成立日

    # HFD_Stock_M = 'Y:\\合成数据\\逐笔1min\\逐笔1min'  # 高频分钟数据
    # HFD_Stock_Depth = 'Y:\\合成数据\\十档Vwap'  # 高频十档盘口数据
    # HFD_Stock_Depth_1min = 'Y:\\合成数据\\十档1min\\因子数据'  # 高频十档分钟数据
    # HFD_Stock_CF = 'Y:\\合成数据\\逐笔资金流向'  # 逐笔资金流向
    # HFD_MidData = 'Y:\\合成数据\\MidData'  # 高频因子中间数据

    HFD_Stock_M = 'B:\\合成数据\\逐笔1min\\逐笔1min'  # 高频分钟数据
    HFD_Stock_Depth = 'B:\\合成数据\\十档Vwap'  # 高频十档盘口数据
    HFD_Stock_Depth_1min = 'B:\\合成数据\\十档1min\\十档一分钟样本内'  # 高频十档分钟数据
    HFD_Stock_CF = 'B:\\合成数据\\逐笔资金流向'  # 逐笔资金流向
    HFD_MidData = 'B:\\合成数据\\MidData'  # 高频因子中间数据
    # HFD_MidData = 'A:\\Test'
    HFD = 'A:\\DataBase\\HFD'  # 高频数据存储地址


@unique
class SpecialName(Enum):
    GROUP = 'group'

    STOCK_WEIGHT = 'stockWeight'
    CSI_300 = '000300.SH'
    CSI_500 = '000905.SH'
    CSI_800 = '000906.SH'
    WI_A = 'Wind_A'

    INDUSTRY_FLAG = 'indexCode'
    CSI_300_INDUSTRY_WEIGHT = 'csi_300_weight'
    CSI_500_INDUSTRY_WEIGHT = 'csi_500_weight'
    CSI_50_INDUSTRY_WEIGHT = 'csi_50_weight'

    CSI_300_INDUSTRY_MV = 'csi_300_mv'
    CSI_500_INDUSTRY_MV = 'csi_500_mv'
    CSI_50_INDUSTRY_MV = 'csi_50_mv'
    ANN_DATE = 'date'
    REPORT_DATE = 'report_date'


@unique
class PriceVolumeName(Enum):
    CLOSE = 'close'
    OPEN = 'open'
    HIGH = 'high'
    LOW = 'low'

    CLOSE_ADJ = 'closeAdj'
    OPEN_ADJ = 'openAdj'
    HIGH_ADJ = 'highAdj'
    LOW_ADJ = 'lowAdj'

    Up_Down = 'priceLimit'
    ISST = 'isst'
    LIST_DAYS_NUM = 'period2list'
    LIST_BOARD = 'listBoard'

    AMOUNT = 'amount'
    VOLUME = 'volume'

    ADJ_FACTOR = 'adjfactor'

    LIQ_MV = 'liqMv'
    TOTAL_MV = 'totalMv'


@unique
class BroadName(Enum):
    STIB = '科创板'


@unique
class Exchange(Enum):
    SSE = 'SH'
    SZSE = 'SZ'
