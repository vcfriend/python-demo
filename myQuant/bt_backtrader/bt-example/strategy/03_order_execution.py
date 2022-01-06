from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import os.path
import time
import sys


import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class OrderExecutionStrategy(bt.Strategy):
    params = (
        ('smaperiod', 15),
        ('exectype', 'Market'),
        ('perc1', 3),
        ('perc2', 1),
        ('valid', 4),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log('ORDER ACCEPTED/SUBMITTED', dt=order.created.dt)
            self.order = order
            return

        if order.status in [order.Expired]:
            self.log('BUY EXPIRED')

        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

        # Sentinel to None: new orders allowed
        self.order = None

    def __init__(self):
        # SimpleMovingAverage on main data
        # Equivalent to -> sma = btind.SMA(self.data, period=self.p.smaperiod)
        sma = btind.SMA(period=self.p.smaperiod)

        # CrossOver (1: up, -1: down) close / sma
        self.buysell = btind.CrossOver(self.data.close, sma, plot=True)

        # Sentinel to None: new ordersa allowed
        self.order = None

    def next(self):
        if self.order:
            # An order is pending ... nothing can be done
            return

        # Check if we are in the market
        if self.position:
            # In the maerket - check if it's the time to sell
            if self.buysell < 0:
                self.log('SELL CREATE, %.2f' % self.data.close[0])
                self.sell()

        elif self.buysell > 0:
            if self.p.valid:
                valid = self.data.datetime.date(0) + \
                        datetime.timedelta(days=self.p.valid)
            else:
                valid = None

            # Not in the market and signal to buy
            if self.p.exectype == 'Market':
                self.buy(exectype=bt.Order.Market)  # default if not given

                self.log('BUY CREATE, exectype Market, price %.2f' %
                         self.data.close[0])

            elif self.p.exectype == 'Close':
                self.buy(exectype=bt.Order.Close)

                self.log('BUY CREATE, exectype Close, price %.2f' %
                         self.data.close[0])

            elif self.p.exectype == 'Limit':
                price = self.data.close * (1.0 - self.p.perc1 / 100.0)

                self.buy(exectype=bt.Order.Limit, price=price, valid=valid)

                if self.p.valid:
                    txt = 'BUY CREATE, exectype Limit, price %.2f, valid: %s'
                    self.log(txt % (price, valid.strftime('%Y-%m-%d')))
                else:
                    txt = 'BUY CREATE, exectype Limit, price %.2f'
                    self.log(txt % price)

            elif self.p.exectype == 'Stop':
                price = self.data.close * (1.0 + self.p.perc1 / 100.0)

                self.buy(exectype=bt.Order.Stop, price=price, valid=valid)

                if self.p.valid:
                    txt = 'BUY CREATE, exectype Stop, price %.2f, valid: %s'
                    self.log(txt % (price, valid.strftime('%Y-%m-%d')))
                else:
                    txt = 'BUY CREATE, exectype Stop, price %.2f'
                    self.log(txt % price)

            elif self.p.exectype == 'StopLimit':
                price = self.data.close * (1.0 + self.p.perc1 / 100.0)

                plimit = self.data.close * (1.0 + self.p.perc2 / 100.0)

                self.buy(exectype=bt.Order.StopLimit, price=price, valid=valid,
                         plimit=plimit)

                if self.p.valid:
                    txt = ('BUY CREATE, exectype StopLimit, price %.2f,'
                           ' valid: %s, pricelimit: %.2f')
                    self.log(txt % (price, valid.strftime('%Y-%m-%d'), plimit))
                else:
                    txt = ('BUY CREATE, exectype StopLimit, price %.2f,'
                           ' pricelimit: %.2f')
                    self.log(txt % (price, plimit))


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()

    datapath = '../datas/orcl-1995-2014.txt'

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values before this date
        todate=datetime.datetime(2000, 12, 31),
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    cerebro.addstrategy(
        OrderExecutionStrategy,
        exectype=args.exectype,
        perc1=args.perc1,
        perc2=args.perc2,
        valid=args.valid,
        smaperiod=int(args.smaperiod)
    )
    cerebro.run()

def parse_args():
    parser = argparse.ArgumentParser(
        description='Showcase for Order Execution Types')

    parser.add_argument('--smaperiod', '-s', required=False, default=15,
                        help='Simple Moving Average Period')

    parser.add_argument('--exectype', '-e', required=False, default='Market',
                        help=('Execution Type: Market (default), Close, Limit,'
                              ' Stop, StopLimit'))

    parser.add_argument('--valid', '-v', required=False, default=0, type=int,
                        help='Validity for Limit sample: default 0 days')

    parser.add_argument('--perc1', '-p1', required=False, default=0.0,
                        type=float,
                        help=('%% distance from close price at order creation'
                              ' time for the limit/trigger price in Limit/Stop'
                              ' orders'))

    parser.add_argument('--perc2', '-p2', required=False, default=0.0,
                        type=float,
                        help=('%% distance from close price at order creation'
                              ' time for the limit price in StopLimit orders'))

    return parser.parse_args()

if __name__ == '__main__':
	runstrat()