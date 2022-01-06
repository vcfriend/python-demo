from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

from feeds.amibrokercsv import AmibrokerCSV
from strategy.teststrategy import TestStrategy

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    datapath = '../datas/SET50_H1_2011_2017.csv'

    # Create a Data Feed
#     data = bt.feeds.GenericCSVData(
#         dataname=datapath,
#         dtformat='%Y%m%d',
#         tmformat='%H%M%S',
#         # Do not pass values before this date
#         fromdate=datetime.datetime(2011, 6, 1),
#         # Do not pass values after this date
#         todate=datetime.datetime(2011, 8, 31),
#         datetime=0,
#         time=1,
#         open=2,
#         high=3,
#         low=4,
#         close=5,
#         volume=-1,
#         openinterest=-1,
#
#     )
    data = AmibrokerCSV(
		dataname=datapath,
	)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    cerebro.addstrategy(TestStrategy)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
