#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
#
# 本程序是免费软件：您可以根据自由软件基金会发布的 GNU 通用公共许可条款
# （许可的第 3 版或（由您选择）任何更高版本）重新分发和修改它。
# 分发此程序的目的是希望它有用，但不提供任何保证；甚至没有对适销性或特定用途适用性的默示保证。
# 有关详细信息，请参阅 GNU 通用公共许可证。
# 您应该已经收到了一份 GNU 通用公共许可证的副本以及该程序。如果没有，
# 请参阅 <http:www.gnu.orglicenses>。
#
###############################################################################
from __future__ import (absolute_import, division, print_function,)
#                        unicode_literals)

import argparse
import datetime

import backtrader as bt
import backtrader.feeds as btfeeds


class St(bt.Strategy):
    def next(self):
        print(','.join(str(x) for x in [
            self.data.datetime.datetime(),
            self.data.open[0], self.data.high[0],
            self.data.high[0], self.data.close[0],
            self.data.volume[0]]))


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()

    data = btfeeds.GenericCSVData(
        dataname=args.data,
        dtformat='%d/%m/%y',
        # tmformat='%H:%M:%S',  # 已经是默认值
        # datetime=0,  # 默认位置
        date=0,  # 日期位置
        time=1,  # 时间位置
        open=5,  # 打开位置
        high=5,
        low=5,
        close=5,
        volume=7,
        openinterest=-1,  # -1 for not present
        timeframe=bt.TimeFrame.Ticks)

    cerebro.resampledata(data,
                         timeframe=bt.TimeFrame.Ticks,
                         compression=args.compression)

    cerebro.addstrategy(St)

    cerebro.run()
    if args.plot:
        cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='BidAsk to OHLC')

    parser.add_argument('--data', required=False,
                        default='../../datas/bidask2.csv',
                        help='Data file to be read in')

    parser.add_argument('--compression', required=False, default=2, type=int,
                        help='How much to compress the bars')

    parser.add_argument('--plot', required=False, action='store_true',
                        help='Plot the vars')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
