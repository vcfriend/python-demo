from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse

import backtrader as bt

from strategy.teststrategy import TestStrategy


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Add a strategy
    # 	cerebro.addstrategy(bt.Strategy)
    cerebro.addstrategy(TestStrategy)

    # Load the Data
    # 	datapath = args.dataname or '../datas/2006-day-001.txt'
    datapath = '../datas/2006-min-005.txt'
    data = bt.feeds.BacktraderCSVData(
        dataname=datapath)

    # 参数时间框架转换的方便字典
    tframes = dict(
        second=bt.TimeFrame.Seconds,
        minute=bt.TimeFrame.Minutes,
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months
    )

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Resample the data
    if args.oldrs:
        # 旧的重采样器，完全弃用
        data = bt.DataResampler(
            dataname=data,
            timeframe=tframes[args.timeframe],
            compression=args.compression)

        # 添加重采样数据而不是原始数据
        cerebro.adddata(data)
    else:
        # New resampler
        cerebro.resampledata(
            data,
            name='data_{0}'.format(args.timeframe),
            timeframe=tframes[args.timeframe],
            compression=args.compression)

    # Run over everything
    cerebro.run()

    # Plot the result
    cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Resample down to minutes')

    parser.add_argument('--dataname', default='', required=False,
                        help='File Data to Load')

    parser.add_argument('--oldrs', required=False, action='store_true',
                        help='Use deprecated DataResampler')

    parser.add_argument('--timeframe', default='daily', required=False,
                        choices=['second', 'minute', 'daily', 'weekly', 'monthly'],
                        help='Timeframe to resample to')

    parser.add_argument('--compression', default=1, required=False, type=int,
                        help='Compress n bars into 1')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
