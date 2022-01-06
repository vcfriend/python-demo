from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import argparse
import datetime
import colorama

import backtrader as bt

class TrailStrategy(bt.Strategy):
    params = dict(
        ma=bt.ind.SMA,
        period1 = 10,
        period2 = 30,
        trailamount=0.0,
        trailpercent=0.0,
    )

    def __init__(self):
        ma1 = self.p.ma(period=self.p.period1)
        ma2 = self.p.ma(period=self.p.period2)
        self.crup = bt.ind.CrossUp(ma1, ma2)
        self.order = None

    def next(self):
        print(f"{self.datetime.date()}: Open: {round(self.data.open[0],2)}, High: {round(self.data.high[0],2)}, Low: {round(self.data.low[0],2)}, Close: {round(self.data.close[0],2)}")
        if not self.position:
            if self.crup:
                o = self.buy()
                self.order = None
                print(colorama.Style.BRIGHT + colorama.Fore.GREEN + ' BUY  ' + colorama.Fore.RESET + colorama.Style.RESET_ALL, end='')

        elif self.order is None:
#             plimit = self.data.close + 10
#             self.order = self.sell(exectype=bt.Order.StopTrail, plimit=plimit, trailamount=self.p.trailamount, trailpercent=self.p.trailpercent)
            self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=self.p.trailamount, trailpercent=self.p.trailpercent)
            print(colorama.Style.BRIGHT + colorama.Fore.RED + ' SELL ' + colorama.Fore.RESET + colorama.Style.RESET_ALL)

            if self.p.trailamount:
                trigger_price = self.data.close - self.p.trailamount
            else:
                trigger_price = self.data.close * (1.0 - self.p.trailpercent)
            print(colorama.Fore.RED + f"{self.datetime.date()}: Close: {round(self.data.close[0],2)}, Trigger Price: {round(self.order.created.price,2)}, Ideal Trigger Price: {round(trigger_price,2)}" + colorama.Fore.RESET)
        else:
            if self.p.trailamount:
                trigger_price = self.data.close - self.p.trailamount
            else:
                trigger_price = self.data.close * (1.0 - self.p.trailpercent)
            print(colorama.Fore.RED + f"{self.datetime.date()}: Close: {round(self.data.close[0],2)}, Trigger Price: {round(self.order.created.price,2)}, Ideal Trigger Price: {round(trigger_price,2)}" + colorama.Fore.RESET)

    def notify_order(self, order):
#         print(f"{self.data.datetime.date(0)}: Type {'Buy ' * order.isbuy() or 'Sell'}, Status {order.getstatusname()}, Size {order.size}, Price: {'NA' if not order.price else round(order.price, 5)}")
        if order.status == order.Completed:
            print('-- Notify -- {}: Created: {} Type {} Price: {} Size: {}'.format(self.data.datetime.date(0), bt.num2date(order.created.dt), 'Buy ' * order.isbuy() or 'Sell', order.created.price,order.created.size))



def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed
    data0 = bt.feeds.BacktraderCSVData(dataname='../datas/2005-2006-day-001.txt')
    cerebro.adddata(data0)

    trailamount = 50
    trailpercent = 0

    # Strategy
    cerebro.addstrategy(TrailStrategy, trailamount=trailamount, trailpercent=trailpercent)

    # Execute
    cerebro.run()

    if args.plot:  # Plot if requested to
        cerebro.plot()


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'StopTrail'
        )
    )


    parser.add_argument('--plot', required=False, default='',
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)

if __name__ == '__main__':
    runstrat()