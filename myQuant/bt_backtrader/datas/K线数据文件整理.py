import pandas as pd
from datetime import datetime

df = pd.read_csv(
    filepath_or_buffer='RB指数99-1m-2009-03-27-2021-12-31.csv',
    sep=',',
    index_col='datetime',
    parse_dates=['datetime'],
    date_parser=lambda x: pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S'),  # 时间解析的格式，进行毫,
    # date_parser=lambda x: pd.to_datetime(x, format='%Y%m%d%H%M%S.%f'),  # 时间解析的格式，进行毫,
    # usecols=['datetime', 'open', 'high', 'low', 'close', 'volume'],
    usecols=['datetime', 'open', 'close'],
)
# 将日期列设置为索引
# df.set_index('datetime', inplace=True)
dt_start = datetime.strptime('2009-03-27', '%Y-%m-%d').date()
dt_end = datetime.strptime('2009-04-27', '%Y-%m-%d').date()
# df = df[dt_start:dt_end]
# df[''] = pd.Series()  # 增加空列，为了后续读取文件方便识别

rule_type = '5T'  # 周期单位: 5T=5分钟 1H=1小时 1D=1天 1W=1周
# rule=rule_type, label='right', closed='right'
period_df = df.resample(rule=rule_type, label='left', closed='left').agg(
    {'open': 'first',
     # 'high': 'max',
     # 'low': 'min',
     'close': 'last',
     # 'volume': 'sum'
     }).dropna()

filename = 'SQRBOC-5m-20090327-20211231.csv'
period_df.to_csv(
    path_or_buf=filename,  # 文件保存路径
    sep=',',  # 分隔符
    header=True,  # 导出列标签
    date_format='%Y-%m-%d %H:%M:%S',  # 时期格式化字符串
    float_format='%.0f',  # 浮点数格式化字符串保留的小数位数
)
print(period_df)
