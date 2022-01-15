import pandas as pd

df = pd.read_csv(
    filepath_or_buffer='DQC00-1m-2021.txt',
    sep=',',
    index_col=0,
    parse_dates=['datetime'],
    date_parser=lambda x: pd.to_datetime(x, format='%Y%m%d%H%M%S.%f'),  # 时间解析的格式，进行毫,
)
df[''] = pd.Series()  # 增加空列，为了后续读取文件方便识别
print(df)

filename = 'DQC00-1m-20210301.csv'
df.to_csv(
    path_or_buf=filename,  # 文件保存路径
    sep=',',  # 分隔符
    header=True,  # 导出列标签
    date_format='%Y%m%d%H%M%S',  # 时期格式化字符串
    float_format='%.0f',  # 浮点数格式化字符串保留的小数位数
)
