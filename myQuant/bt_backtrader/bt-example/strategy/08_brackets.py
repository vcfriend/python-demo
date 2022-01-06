from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import argparse
import datetime

import backtrader as bt

class BracketsStrategy(bt.Strategy):
    params = dict(
        ma = bt.ind.SMA,
        period1 = 5,
        period2 = 15,
    )

    def __init__(self):
        ma1 = self.p.ma(period=self.p.period1)
        ma2 = self.p.ma(period=self.p.period2)
        self.cross = bt.ind.CrossOver(ma1, ma2)
        self.orefs = list()

    def next(self):
        date = self.data.datetime.date()
        close = self.data.close[0]

        print(f"{date}: Close: {close}, Position Size: {self.position.size}")

        if self.orefs:
            return

        if not self.position:
            if date == datetime.datetime(2005,3,3).date():
                # Enter with a limit order to go short to try and catch price near top
                entry = close + (0.005 * close)
                short_tp = entry - (0.02 * entry)
                short_stop = entry + (0.02 * entry)
                ord = self.sell_bracket(limitprice=short_tp, price=entry, stopprice=short_stop, exectype=bt.Order.Limit)

                self.orefs = [o.ref for o in ord]

#             if self.cross > 0.0: # cross up
#                 # Enter with market order
#                 long_tp = close + (0.02 * close)
#                 long_stop = close - (0.02 * close)
#                 ord = self.buy_bracket(limitprice=long_tp, stopprice=long_stop, exectype=bt.Order.Market)
#                 self.orefs = [o.ref for o in ord]
#
#             elif self.cross < 0.00: # cross down
#                 # Enter with stop order to go short and catch price on way down
#                 entry = close - (0.005 * close)
#                 short_tp = entry - (0.02 * entry)
#                 short_stop = entry + (0.02 * entry)
#                 valid = datetime.timedelta(3)
#                 trigger_valid = datetime.timedelta(15)
#                 ord = self.sell_bracket(limitprice=short_tp, price=entry, stopprice=short_stop, exectype=bt.Order.Stop, valid=valid, stopargs={'valid': trigger_valid}, limitargs={'valid': trigger_valid})
#                 self.orefs = [o.ref for o in ord]


    def notify_order(self, order):
        print(f"{self.data.datetime.date(0)}: Order ref: {order.ref}, Type {'Buy ' * order.isbuy() or 'Sell'}, Status {order.getstatusname()}, Size {order.size}, Price: {'NA' if not order.price else round(order.price, 5)}")
        if order.status == order.Completed:
            print('Created: {} Price: {} Size: {}'.format(bt.num2date(order.created.dt), order.created.price,order.created.size))
        if not order.alive() and order.ref in self.orefs:
            self.orefs.remove(order.ref)

def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed
    data0 = bt.feeds.BacktraderCSVData(dataname='../datas/2005-2006-day-001.txt')
    cerebro.adddata(data0)

    # Strategy
    cerebro.addstrategy(BracketsStrategy)

    # Execute
    cerebro.run()

    if args.plot:  # Plot if requested to
        cerebro.plot()


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Order Brackets'
        )
    )



    parser.add_argument('--plot', required=False, default='',
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)

if __name__ == '__main__':
    runstrat()