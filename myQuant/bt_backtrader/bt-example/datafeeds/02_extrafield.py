from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

from feeds.amibrokercsvpe import AmibrokerCSVPE

class MyStrategy(bt.Strategy):
	def __init__(self):
		bt.indicators.SMA(self.data.pe, period=1, subplot=True, plotname="PE")

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    datapath = '../datas/SET50_H1_2011_2017_pe.csv'

    # Create a Data Feed
    data = AmibrokerCSVPE(
        dataname=datapath,
    )

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    cerebro.addstrategy(MyStrategy)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()
    cerebro.plot(volume=False)

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
