import pandas as pd
from enum import Enum


class head(Enum):
    """枚举列表头"""
    DATE = 0  # date所在列
    OPEN = 1
    HIGH = 2
    LOW = 3
    CLOSE = 4
    VOLUME = 5


df = pd.read_csv(
    filepath_or_buffer='603228.SH-day.csv',
    sep=',',
    header=0,  # 标头
    index_col=[0],  # 设置行索引
    parse_dates=[0],  # 解析时间
    date_parser=lambda x: pd.to_datetime(x, format='%Y-%m-%d %H:%M'),  # 时间解析的格式
    # usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest'],
    usecols=[head.DATE.value, head.OPEN.value, head.HIGH.value, head.LOW.value, head.CLOSE.value, head.VOLUME.value],
)
# 将日期列，设置成index
# df.index = pd.to_datetime(df.iloc[:,0], format='%Y-%m-%d')
print(df.head())

rule_type = '1W'  # 周期单位: 5T=5分钟 1H=1小时 1D=1天 1W=1周

head_ = list(df)
head_open = list(df)[head.OPEN.value - 1]
head_high = list(df)[head.HIGH.value - 1]
head_low = list(df)[head.LOW.value - 1]
head_close = list(df)[head.CLOSE.value - 1]
head_volume = list(df)[head.VOLUME.value - 1]

period_df = df.resample(rule=rule_type, label='left', closed='left').agg(
    {head_open: 'first',
     head_high: 'max',
     head_low: 'min',
     head_close: 'last',
     head_volume: 'sum',
     })
print('返回每一列缺失值统计个数:', period_df.isnull().sum())
period_df = period_df.dropna(axis=0, how='any')
print('检查数据中是否有缺失值:', period_df.isnull().any())
# 保存文件
period_df.to_csv(
    path_or_buf='603228.SH-week.csv',
    sep=',',  # 分隔符
    header=True,  # 导出列标签
    date_format='%Y-%m-%d',  # 时期格式化字符串
    float_format='%.2f',  # 浮点数格式化字符串
)
print(period_df.head())
