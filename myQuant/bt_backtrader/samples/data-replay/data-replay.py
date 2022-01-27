#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class SMAStrategy(bt.Strategy):
    params = (
        ('period', 10),
        ('onlydaily', False),
    )

    def log(self, txt, dt=None):
        """ Logging function for this strategy"""
        dt = dt or self.datas[0].datetime
        print('%s, %s: %s' % (dt._owner._name, dt.datetime(0).isoformat(), txt))

    def __init__(self):
        self.sma = btind.SMA(self.data, period=self.p.period)

    def start(self):
        self.counter = 0

    def prenext(self):
        self.counter += 1
        print('prenext len%d - counter %d' % (len(self), self.counter))

    def next(self):
        self.counter += 1
        self.log('---next len %d - counter %d' % (len(self), self.counter))



def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    cerebro.addstrategy(
        SMAStrategy,
        # args for the strategy
        period=args.period,
    )

    # Load the Data
    datapath = args.dataname or '../../datas//2006-day-001.txt'
    data = btfeeds.BacktraderCSVData(
        dataname=datapath)

    tframes = dict(
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months)

    # 用于参数时间帧转换的方便字典重新采样数据
    if args.oldrp:
        # 旧的重采样器，完全弃用
        data = bt.DataReplayer(
            dataname=data,
            timeframe=tframes[args.timeframe],
            compression=args.compression)
    else:
        data.replay(
            timeframe=tframes[args.timeframe],
            compression=args.compression)

    # 首先添加原始数据 - 更小的时间范围
    cerebro.adddata(data)

    # Run over everything
    cerebro.run(preload=False)

    # Plot the result
    cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Pandas test script')

    parser.add_argument('--dataname', default='', required=False,
                        help='要加载的文件数据')

    parser.add_argument('--oldrp', required=False, action='store_true',
                        help='使用已弃用的 DataReplayer')

    parser.add_argument('--timeframe', default='weekly', required=False,
                        choices=['daily', 'weekly', 'monthly'],
                        help='重新采样到的时间范围')

    parser.add_argument('--compression', default=1, required=False, type=int,
                        help='将 n 条压缩为 1')

    parser.add_argument('--period', default=10, required=False, type=int,
                        help='适用于指标的时期')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
