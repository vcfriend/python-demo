#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
"""版权所有 (C) 2015-2020 Daniel Rodriguez 此程序是免费软件：
您可以根据自由软件基金会发布的 GNU 通用公共许可证（许可证的第 3 版）或（在您的选项）任何更高版本。
分发此程序的目的是希望它有用，但不提供任何保证；甚至没有对适销性或特定用途适用性的默示保证。
有关详细信息，请参阅 GNU 通用公共许可证。您应该已经收到了一份 GNU 通用公共许可证的副本以及该程序。
如果没有，请参阅 <http:www.gnu.orglicenses>。
"""
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds
import backtrader.filters as btfilters


def runstrat():
    args = parse_args()

    # 创建一个大脑实体
    cerebro = bt.Cerebro(stdstats=False)

    # 添加策略
    cerebro.addstrategy(bt.Strategy)

    # 从 args 中获取日期
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    data = btfeeds.BacktraderCSVData(
        dataname=args.data,
        fromdate=fromdate,
        todate=todate)

    if args.calendar:
        if args.fprice is not None:
            args.fprice = float(args.fprice)

        data.addfilter(
            btfilters.CalendarDays,
            fill_price=args.fprice,
            fill_vol=args.fvol)

    # 添加重新样本数据,而不是原始数据
    cerebro.adddata(data)

    # 如果需要，添加一个简单的移动平均线
    if args.sma:
        cerebro.addindicator(btind.SMA, period=args.period)

    # 使用 CSV 添加作家
    if args.writer:
        cerebro.addwriter(bt.WriterFile, csv=args.wrcsv)

    # Run over everything
    cerebro.run()

    # 如果要求绘图
    if args.plot:
        cerebro.plot(style='bar', numfigs=args.numfigs, volume=False)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Calendar Days Filter Sample')

    parser.add_argument('--data', '-d',
                        default='../../datas/2006-day-001.txt',
                        help='添加到系统的数据')

    parser.add_argument('--fromdate', '-f',
                        default='2006-01-01',
                        help='YYYY-MM-DD 格式的开始日期')

    parser.add_argument('--todate', '-t',
                        default='2006-12-31',
                        help='YYYY-MM-DD 格式的开始日期')

    parser.add_argument('--calendar', '-cal', required=False,
                        action='store_true',
                        help='添加 CalendarDays 过滤器')

    parser.add_argument('--fprice', required=False, default=None,
                        help='用作价格的填充（前一收盘时无）')

    parser.add_argument('--fvol', required=False, default=0.0,
                        type=float,
                        help='用作缺失柱的填充量 (def: 0.0)')

    parser.add_argument('--sma', required=False,
                        action='store_true',
                        help='添加一个简单的移动平均线')

    parser.add_argument('--period', default=15, type=int,
                        help='适用于简单移动平均线的时期')

    parser.add_argument('--writer', '-w', action='store_true',
                        default='True',
                        help='将作家添加到 cerebro')

    parser.add_argument('--wrcsv', '-wc', action='store_true',
                        default='./out.csv',
                        help='在编写器中启用 CSV 输出')

    parser.add_argument('--plot', '-p', action='store_true',
                        default='True',
                        help='绘制读取的数据')

    parser.add_argument('--numfigs', '-n', default=1,
                        help='使用 numfigs 数字绘图')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
