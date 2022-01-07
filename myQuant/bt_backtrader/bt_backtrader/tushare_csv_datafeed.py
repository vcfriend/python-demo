#!/usr/bin/env python
# -*- encoding: utf-8 -*-
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
import datetime
import pandas as pd
import tushare as ts


# 加载本地csv文件数据
def get_csv_daily_data(stock_id="600016.SH", start="20190101", end="20191231"):
    """从本地股票日线csv文件中取得DataFeed对象

    Args:
        stock_id (str, optional): tushare格式的股票代码. Defaults to "600016.SH".

    Raises:
        Exception: 本地文件无法找到

    Returns:
        [type]: backtrader.feeds.pandafeed.PandasData对象
    """
    # 日期格式转换
    dt_start = datetime.datetime.strptime(start, "%Y%m%d")
    dt_end = datetime.datetime.strptime(end, "%Y%m%d")

    # 文件存放地址
    file_path = os.path.join('./fd_data/' + stock_id + ".csv")
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

    # print(df.shape[0])
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
    datapath = os.path.join('fd_data/600016.SH.csv')
    # 日期格式转换
    dt_start = datetime.datetime.strptime(start, "%Y%m%d")
    dt_end = datetime.datetime.strptime(end, "%Y%m%d")
    # 读取文件
    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(2000, 1, 1),
        todate=datetime.datetime(2000, 12, 31),
        nullvalue=0.0,
        dtformat=('%Y%m%d'),
        datetime=1,
        high=3,
        low=4,
        open=2,
        close=5,
        volume=9,
        openinterest=-1
    )
    return data


def get_tushare_online_daily_data():
    """
    将A股票日线数据返回BT Data
    """
    stock_id = "000001.SZ"
    start = "20190101"
    end = "20191231"
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

        print(df.shape[0])
        # print(df.info())
        print(df.head())

        data = bt.feeds.PandasData(dataname=df, fromdate=dt_start, todate=dt_end)

        return data
    except Exception as err:
        print("下载{0}完毕失败！")
        print("失败原因 = " + str(err))


if __name__ == "__main__":
    # 读取从tushare下载的日线数据文件：
    data = get_csv_daily_data()

    # # 读取csv文件
    # data = get_csv_GenericCSVData()

    # 读取在线数据
    # data = get_tushare_online_daily_data()

    print('data', data)
    print(type(data))
    os.system("pause")
