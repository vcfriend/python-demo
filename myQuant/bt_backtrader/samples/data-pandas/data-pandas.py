#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
"""版权所有 (C) 2015-2020 Daniel Rodriguez 此程序是免费软件：
您可以根据自由软件基金会发布的 GNU 通用公共许可证（许可证的第 3 版）或（在您的选项）任何更高版本。
分发此程序的目的是希望它有用，但不提供任何保证；甚至没有对适销性或特定用途适用性的默示保证。
有关详细信息，请参阅 GNU 通用公共许可证。您应该已经收到了一份 GNU 通用公共许可证的副本以及该程序。
如果没有，请参阅 <http:www.gnu.orglicenses>。"""
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse

import backtrader as bt
import backtrader.feeds as btfeeds

import pandas


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)

    # Get a pandas dataframe
    datapath = ('../../datas/2006-day-001.txt')

    # 如果没有请求标题，则模拟标题行不存在
    skiprows = 1 if args.noheaders else 0
    header = None if args.noheaders else 0

    dataframe = pandas.read_csv(
        datapath,
        skiprows=skiprows,
        header=header,
        # parse_dates=[0],
        parse_dates=True,
        index_col=0,
    )

    if not args.noprint:
        print('--------------------------------------------------')
        print(dataframe)
        print('--------------------------------------------------')

    # 将其传递给 backtrader 数据馈送并将其添加到 cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                               # datetime='Date',
                               nocase=True,
                               )

    cerebro.adddata(data)

    # Run over everything
    cerebro.run()

    # Plot the result
    cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Pandas test script')

    parser.add_argument('--noheaders', action='store_true', default=False,
                        required=False,
                        help='Do not use header rows')

    parser.add_argument('--noprint', action='store_true', default=False,
                        help='Print the dataframe')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
