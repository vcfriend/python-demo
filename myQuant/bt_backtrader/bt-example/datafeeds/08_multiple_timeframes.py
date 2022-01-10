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
    #	cerebro.addstrategy(bt.Strategy)
    cerebro.addstrategy(TestStrategy)

    # Load the Data
    datapath = '../datas/2006-day-001.txt'
    data = bt.feeds.BacktraderCSVData(
        dataname=datapath)

    cerebro.adddata(data)

    # Resample the data
    if args.noresample:
        datapath = '../datas/2006-week-001.txt'
        data2 = bt.feeds.BacktraderCSVData(
            dataname=datapath)
        cerebro.adddata(data2)
    else:
        # New resampler
        cerebro.resampledata(
            data,
            name="data_resa_1W",
            timeframe=bt.TimeFrame.Weeks,
            compression=1)

    # Run over everything
    cerebro.run()

    # Plot the result
    cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Resample down to minutes')

    parser.add_argument('--noresample', action='store_true',
                        help='Do not resample, rather load larger timeframe')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
