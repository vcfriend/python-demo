# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 12:18:17 2020

@author: horace pei
"""
#############################################################
# import
#############################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os, sys
import pandas as pd
import backtrader as bt


#############################################################
# global const values
#############################################################
#############################################################
# static function
#############################################################
#############################################################
# class
#############################################################
# Create a Stratey
class TestStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])


#############################################################
# global values
#############################################################
#############################################################
# global function
#############################################################
def get_dataframe():
    # Get a pandas dataframe
    datapath = './data/stockinfo.csv'
    tmpdatapath = './data/stockinfo_tmp.csv'
    print('-----------------------read csv---------------------------')
    dataframe = pd.read_csv(datapath,
                            skiprows=0,
                            header=0,
                            parse_dates=True,
                            index_col=0)
    # print(dataframe)
    # print('--------------------------------------------------')
    # print('-----------------------change time------------------------')
    dataframe.trade_date = pd.to_datetime(dataframe.trade_date, format="%Y%m%d")
    # print(dataframe)
    # print('--------------------------------------------------')
    # print('-----------------------add openinterest-------------------')
    dataframe['openinterest'] = '0'
    # print(dataframe)
    # print('--------------------------------------------------')
    # print('-----------------------make feedsdf-----------------------')
    feedsdf = dataframe[['trade_date', 'open', 'high', 'low', 'close', 'vol', 'openinterest']]
    # print(feedsdf)
    # print('--------------------------------------------------')
    # print('-----------------------change columns---------------------')
    feedsdf.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest']
    # print(feedsdf)
    # print('--------------------------------------------------')
    # print('-----------------------change index-----------------------')
    feedsdf.set_index(keys='datetime', inplace=True)
    # print(feedsdf)
    # print('--------------------------------------------------')
    feedsdf.iloc[::-1].to_csv(tmpdatapath)
    feedsdf = pd.read_csv(tmpdatapath, skiprows=0, header=0, parse_dates=True, index_col=0)
    if os.path.isfile(tmpdatapath):
        os.remove(tmpdatapath)
        print(tmpdatapath + " removed!")
    return feedsdf


########################################################################
# main
########################################################################
if __name__ == '__main__':
    # Create a cerebro entity(创建cerebro)
    cerebro = bt.Cerebro()
    # Add a strategy(加入自定义策略)
    cerebro.addstrategy(TestStrategy)
    # Get a pandas dataframe(获取dataframe格式股票数据)
    feedsdf = get_dataframe()
    # Pass it to the backtrader datafeed and add it to the cerebro(加入数据)
    data = bt.feeds.PandasData(dataname=feedsdf)
    cerebro.adddata(data)
    # Set our desired cash start(给经纪人，可以理解为交易所股票账户充钱)
    cerebro.broker.setcash(100000.0)
    # Print out the starting conditions(输出账户金额)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # Run over everything(执行回测)
    cerebro.run()
    # Print out the final result(输出账户金额)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
