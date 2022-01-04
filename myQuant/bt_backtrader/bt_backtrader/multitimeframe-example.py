from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse

import backtrader as bt
import backtrader.feeds as btfeeds

# Load the Data
datapath = args.dataname or '../../datas/2006-day-001.txt'
data = btfeeds.BacktraderCSVData(dataname=datapath)
cerebro.adddata(data)  # First add the original data - smaller timeframe

tframes = dict(daily=bt.TimeFrame.Days, weekly=bt.TimeFrame.Weeks,
               monthly=bt.TimeFrame.Months)

# Handy dictionary for the argument timeframe conversion
# Resample the data
if args.noresample:
    datapath = args.dataname2 or '../../datas/2006-week-001.txt'
    data2 = btfeeds.BacktraderCSVData(dataname=datapath)
    # And then the large timeframe
    cerebro.adddata(data2)
else:
    cerebro.resampledata(data, timeframe=tframes[args.timeframe],
                         compression=args.compression)

# Run over everything
cerebro.run()