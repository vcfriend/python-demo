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


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)

    # Load the Data
    datapath = args.dataname or '../../datas/2006-day-001.txt'
    data = btfeeds.BacktraderCSVData(
        dataname=datapath)

    # 参数时间框架转换的方便字典
    tframes = dict(
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months)

    # 重新采样数据
    if args.oldrs:
        # 旧的重采样器，完全弃用
        data = bt.DataResampler(
            dataname=data,
            timeframe=tframes[args.timeframe],
            compression=args.compression)

        # 添加重采样数据而不是原始数据
        cerebro.adddata(data)
    else:
        # 新的重采样器
        cerebro.resampledata(
            data,
            timeframe=tframes[args.timeframe],
            compression=args.compression)

    # Run over everything
    cerebro.run()

    # Plot the result
    cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        description='重新采样到几分钟')

    parser.add_argument('--dataname', default='', required=False,
                        help='要加载的文件数据')

    parser.add_argument('--oldrs', required=False, action='store_true',
                        help='使用已弃用的 DataResampler')

    parser.add_argument('--timeframe', default='weekly', required=False,
                        choices=['daily', 'weekly', 'monthly'],
                        help='重新采样到的时间范围')

    parser.add_argument('--compression', default=1, required=False, type=int,
                        help='将 n 条压缩为 1')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
