from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import itertools

# The above could be sent to an independent module
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind

from observers.mtradeobserver import MTradeObserver


class MultiTradeStrategy(bt.Strategy):
    '''This strategy buys/sells upong the close price crossing
    upwards/downwards a Simple Moving Average.
    It can be a long-only strategy by setting the param "onlylong" to True
    '''
    params = dict(
        period=15,
        stake=1,
        printout=True,
        onlylong=False,
        mtrade=True,
    )

    def log(self, txt, dt=None):
        if self.p.printout:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # To control operation entries
        self.order = None

        # Create SMA on 2nd data
        sma = btind.MovAv.SMA(self.data, period=self.p.period)
        # Create a CrossOver Signal from close an moving average
        self.signal = btind.CrossOver(self.data.close, sma)

        # To alternate amongst different tradeids
        if self.p.mtrade:
            self.tradeid = itertools.cycle([0, 1, 2])
        else:
            self.tradeid = itertools.cycle([0])

    def next(self):
        if self.order:
            return  # if an order is active, no new orders are allowed

        if self.signal > 0.0:  # cross upwards
            if self.position:
                self.log('CLOSE SHORT , %.2f' % self.data.close[0])
                self.close(tradeid=self.curtradeid)

            self.log('BUY CREATE , %.2f' % self.data.close[0])
            self.curtradeid = next(self.tradeid)
            self.buy(size=self.p.stake, tradeid=self.curtradeid)

        elif self.signal < 0.0:
            if self.position:
                self.log('CLOSE LONG , %.2f' % self.data.close[0])
                self.close(tradeid=self.curtradeid)

            if not self.p.onlylong:
                self.log('SELL CREATE , %.2f' % self.data.close[0])
                self.curtradeid = next(self.tradeid)
                self.sell(size=self.p.stake, tradeid=self.curtradeid)

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if order.isbuy():
                buytxt = 'BUY COMPLETE, %.2f' % order.executed.price
                self.log(buytxt, order.executed.dt)
            else:
                selltxt = 'SELL COMPLETE, %.2f' % order.executed.price
                self.log(selltxt, order.executed.dt)

        elif order.status in [order.Expired, order.Canceled, order.Margin]:
            self.log('%s ,' % order.Status[order.status])
            pass  # Simply log

        # Allow new orders
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log('TRADE PROFIT, GROSS %.2f, NET %.2f' %
                     (trade.pnl, trade.pnlcomm))

        elif trade.justopened:
            self.log('TRADE OPENED, SIZE %2d' % trade.size)


def runstrat():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()

    datapath = '../datas/orcl-1995-2014.txt'

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
#         fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values before this date
#         todate=datetime.datetime(2000, 12, 31),
        # Do not pass values after this date
        reverse=False)

    # Add the 1st data to cerebro
    cerebro.adddata(data)

    # Add the strategy
    cerebro.addstrategy(MultiTradeStrategy,
                        period=args.period,
                        onlylong=args.onlylong,
                        stake=args.stake)

    # Add the MultiTradeObserver
    cerebro.addobserver(MTradeObserver)

    cerebro.run()
    cerebro.plot()


def parse_args():
    parser = argparse.ArgumentParser(description='MultiTrades')

    parser.add_argument('--period', default=15, type=int,
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--onlylong', '-ol', action='store_true',
                        help='Do only long operations')

    parser.add_argument('--stake', default=1, type=int,
                        help='Stake to apply in each operation')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()