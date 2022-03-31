#!/usr/bin/env python
# coding=utf8
'''
@File    :   tushare_csv_datafeed.py
@Time    :   2020/11/11 00:04:27
@Author  :   Jeffrey Wang
@Version :   1.0
@Contact :   shwangjj@163.com
@Desc    :   基于tushare下载的csv数据源工具代码
'''
import backtrader as bt
import os
import sys
import datetime
import pandas as pd
import backtrader.feeds as btfeeds
import tushare as ts


# 获得根路径
def getRootPath(dirName):
    # 获取文件目录
    curPath = os.path.abspath(os.path.dirname('__file__'))

    # 获取项目根路径，内容为当前项目的名字
    # rootPath = curPath[:curPath.find("项目名\\") + len("项目名\\")]
    rootPath = os.getcwd()[:os.getcwd().find(dirName + "\\") + len(dirName + "\\")]  # 获取项目中相对根路径
    return rootPath


# 从根目录下开始获取其他路径
def getOtherPath(abspath):
    rootPath = getRootPath('')
    dataPath = os.path.abspath(rootPath + abspath)
    return dataPath


# 获得路径，当前文件所在路径
# resource_path方法说明了如何使用sys._MEIPASS变量来访问临时文件夹中的资源。我是在打包exe的时候使用了该功能
def resource_path(relative_path):
    # 是否Bundle Resource
    if getattr(sys, 'frozen', False):
        # running in a bundle
        base_path = sys._MEIPASS
        print('true', base_path)
    else:
        # running live
        base_path = os.path.abspath(".")
        print('false ', base_path)


# 加载本地csv文件数据
def get_csv_pandas_data(filename="orcl-1995-2014.txt", start="20190101", end="20191231"):
    """使用pandas从本地csv文件加载文件数据"""
    # 日期格式转换
    dt_start = datetime.datetime.strptime(start, "%Y%m%d")
    dt_end = datetime.datetime.strptime(end, "%Y%m%d")
    # 获取项目所在根目录
    rootPath = getRootPath('myQuant')
    # 拼接加载路径
    datapath = os.path.join(rootPath + 'bt_backtrader/datas/' + filename)
    print(datapath)

    df = pd.read_csv(
        # Date,Open,High,Low,Close,Adj Close,Volume
        # 1995-01-03,2.179012,2.191358,2.117284,2.117284,1.22,36301200
        filepath_or_buffer=datapath,
        sep=',',  # 分隔符
        # nrows=500,  # 读取行数
        index_col=0,  # 设置行索引
        parse_dates=True,  # 解析时间
        date_parser=lambda x: pd.to_datetime(x, format='%Y%m%d%H%M%S'),  # 时间解析的格式
        usecols=['datetime', 'open', 'high', 'low', 'close', 'volume'],  # 使用的列
    )
    print('df.shape', df.shape)
    # print(df.info())
    # print(df.head())

    # 使用pandas数据源创建交易数据集
    # 把它传递给backtrader数据源，然后添加到cerebro
    data = bt.feeds.PandasData(dataname=df, fromdate=dt_start, todate=dt_end)
    return data


# 加载本地csv文件数据
def get_csv_daily_data(stock_id="600016.SH", start="20190101", end="20191231"):
    """从本地股票日线csv文件中取得DataFeed对象

    Args:
        stock_id (str, optional): tushare格式的股票代码. Defaults to "600016.SH".

    Raises:
        Exception: 本地文件无法找到

    Returns:
        [type]: backtrader.feeds.pandafeed.PandasData对象
        :param stock_id:
        :param end:
        :param start:
    """
    # 日期格式转换
    dt_start = datetime.datetime.strptime(start, "%Y%m%d")
    dt_end = datetime.datetime.strptime(end, "%Y%m%d")

    # 文件存放地址
    file_path = os.path.join('../fd_data/' + stock_id + ".csv")
    if not os.path.exists(file_path):
        print("数据源文件未找到！" + file_path)
        raise Exception("数据源文件未找到！" + file_path)

    # 将csv文件转为pandas.dataframe
    df = pd.read_csv(filepath_or_buffer=file_path)
    # 按日期先后排序
    df.sort_values(by=["trade_date"], ascending=True, inplace=True)
    # 将日期列，设置成index
    df.index = pd.to_datetime(df.trade_date, format='%Y%m%d')
    # 增加一列openinterest
    df['openinterest'] = 0.00
    # 取出特定的列
    df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']]
    # 列名修改成指定的
    df.rename(columns={"vol": "volume"}, inplace=True)

    print('df.shape', df.shape)
    # print(df.info())
    # print(df.head())

    data = bt.feeds.PandasData(dataname=df, fromdate=dt_start, todate=dt_end)
    return data


# 加载本地csv文件数据
def get_csv_GenericCSVData(stock_id="600016.SH", start="20190101", end="20191231"):
    '''
    # 加载本地csv文件数据
    ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount
    600016.SH,20001219,20.0,21.0,18.5,18.56,11.8,6.76,57.29,1563524.56,3058872.084
    '''
    # 日期格式转换
    dt_start = datetime.datetime.strptime(start, "%Y%m%d")
    dt_end = datetime.datetime.strptime(end, "%Y%m%d")
    # 读取文件
    data = btfeeds.GenericCSVData(
        dataname='../fd_data/600016.SH.csv',
        fromdate=dt_start,
        todate=dt_end,
        nullvalue=0.0,
        dtformat=('%Y%m%d'),
        datetime=1,
        open=2,
        high=3,
        low=4,
        close=5,
        volume=9,
        openinterest=-1
    )
    return data


# 从tushare在线读取数据
def get_tushare_online_daily_data(
        stock_id="000001.SZ",
        start="20190101",
        end="20191231",
):
    """将A股票日线数据返回BT Data
    """

    dt_start = datetime.datetime.strptime(start, "%Y%m%d")
    dt_end = datetime.datetime.strptime(end, "%Y%m%d")
    TOKEN = '341d66d4586929fa56f3f987e6c0d5bd23fb2a88f5a48b83904d134b'

    ts.set_token(TOKEN)
    pro = ts.pro_api()

    try:
        # 加载数据
        df = pro.daily(ts_code=stock_id, start_date=start, end_date=end)
        df.sort_values(by=["trade_date"], ascending=True,
                       inplace=True)  # 按日期先后排序
        df.reset_index(inplace=True, drop=True)

        # 开始数据清洗：
        # 按日期先后排序
        df.sort_values(by=["trade_date"], ascending=True, inplace=True)
        # 将日期列，设置成index
        df.index = pd.to_datetime(df.trade_date, format='%Y%m%d')
        # 增加一列openinterest
        df['openinterest'] = 0.00
        # 取出特定的列
        df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']]
        # 列名修改成指定的
        df.rename(columns={"vol": "volume"}, inplace=True)

        print('df.shape', df.shape)
        # print(df.info())
        # print(df.head())

        data = bt.feeds.PandasData(dataname=df, fromdate=dt_start, todate=dt_end)

        return data
    except Exception as err:
        print("下载{0}完毕失败！")
        print("失败原因 = " + str(err))


if __name__ == "__main__":
    # 从pandas文件读取数据
    data = get_csv_pandas_data(filename='SQRB13-5m-20180702-20220319.csv', start='20220101', end='20220322')

    # # 读取从tushare下载的日线数据文件：
    # data = get_csv_daily_data()

    # # 读取csv文件
    # data = get_csv_GenericCSVData()

    # 读取在线数据
    # data = get_tushare_online_daily_data()

    print(data)
    print(type(data))
    # os.system("pause")
