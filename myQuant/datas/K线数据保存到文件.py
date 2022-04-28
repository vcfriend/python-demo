# 金字塔python策略，调用history_bars_date保存K线数据到文件

from PythonApi import *
import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt

print(pd.show_versions())  # 查看系统和包版本信息
print(sys.version)  # 查看python版本信息
print(pd._version)  # 查看包安装路径


#  在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。--(必须实现)
def init(context):
    # 在context中保存全局变量
    context.last_day = 0
    # 初始化保存数据的pandas
    context.data = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    # 1d 为1天，5m 为5分钟周期
    context.rule_type = '5m'
    context.date_start = '20100416'
    context.date_end = '20220428'
    bars = history_bars_date(context.run_info.base_book_id, context.date_start, context.date_end, context.rule_type,
                             context.data)
    print("-------------")
    print(type(bars))
    print(bars.shape)
    print(bars.dtype.name)
    df = pd.DataFrame(bars, columns=context.data)
    print('datetime1: %s, %s' % (df['datetime'].dtype, df['datetime'].loc[0]))

    # 时间格式转换
    df['datetime'] = pd.to_datetime(df['datetime'], format="%Y%m%d%H%M%S")  # date转为时间格式
    # df['date'] = df['datetime'].dt.date
    # df['time'] = df['datetime'].dt.time
    df['date'] = df['datetime'].apply(lambda x: x.strftime('%Y-%m-%d'))  # 添加日期列
    df['time'] = df['datetime'].apply(lambda x: x.strftime('%H:%M:%S'))  # 添加时间列
    # 取出特定列保存
    # df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df[''] = pd.Series()  # df[""] = ""增加空列，为了后续读取文件方便识别
    df[['volume']] = df[['volume']].astype(int)  # 转换指定类数据类型
    df.set_index("datetime", drop=True, inplace=False, append=False)  # 将datetime设置为索引列,drop=True 删除原有列

    print(df.info)
    print("++++++++++++++++")

    filename = r"D:\Users\yalin\Weisoft Stock\%s-%s.csv" % (context.run_info.base_book_id, context.rule_type)
    df.to_csv(
        path_or_buf=filename,  # 文件保存路径
        sep=',',  # 分隔符
        header=True,  # 导出列标签
        # columns=['date', 'time', 'open', 'high', 'low', 'close', 'volume', ''],  # 导出指定列, 日期和时间分开成二列 包括''空列
        columns=['datetime', 'open', 'high', 'low', 'close', 'volume', ''],  # 导出指定列,包括''空列
        date_format='%Y-%m-%d %H:%M:%S',  # 时期格式化字符串
        float_format='%.1f',  # 浮点数格式化字符串保留的小数位数
        index=False,  # 不导出索引列
    )


# before_trading此函数会在每天基准合约的策略交易开始前被调用，当天只会被调用一次。--（选择实现）
def before_trading(context):
    pass


# 你选择的品种的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新。--(必须实现)
def handle_bar(context):
    # 开始编写你的主要的算法逻辑。
    pass

    # 保存的csv文件名
    # csv_name = year+month

    # 存到数据文件中
    # df.to_csv(r"C:/"+csv_name+".csv")

# after_trading函数会在每天交易结束后被调用，当天只会被调用一次。 --（选择实现）
# def after_trading(context):
#    context.last_day = context.now.day


# order_status当委托下单，成交，撤单等与下单有关的动作时，该方法就会被调用。---（选择实现）
# def order_status(context,order):
#    pass

# order_action当查询交易接口信息时返回的通知---（选择实现）
# def order_action(context,type, account, datas)
#       pass

# exit函数会在测评结束或者停止策略运行时会被调用。---（选择实现）
# def exit(context):
#    test_report_none()
# 读取数据文件
# data = pd.read_csv(r'C:\a\201808.csv')
# data = context.data
# data.drop(data.columns[0], axis=1,inplace=True)
