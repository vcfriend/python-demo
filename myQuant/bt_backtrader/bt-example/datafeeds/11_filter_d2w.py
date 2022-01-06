from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import colorama

import backtrader as bt


class St(bt.Strategy):
    params = (
        ('highperiod', 20),
        ('sellafter', 2),
        ('market', False),
    )

    def __init__(self):
        pass

    def start(self):
        self.callcounter = 0
        txtfields = list()
        txtfields.append('Calls')
        txtfields.append('Len Strat')
        txtfields.append('Len Data')
        txtfields.append('Datetime')
        txtfields.append('Open')
        txtfields.append('High')
        txtfields.append('Low')
        txtfields.append('Close')
        txtfields.append('Volume')
        txtfields.append('OpenInterest')
        print(','.join(txtfields))

        self.lcontrol = 0  # control if 1st or 2nd call
        self.inmarket = 0

        # Get the highest but delayed 1 ... to avoid "today"
        self.highest = bt.indicators.Highest(self.data.high,
                                             period=self.p.highperiod,
                                             subplot=False)

    def notify_order(self, order):
        if order.isbuy() and order.status == order.Completed:
            print('-- BUY Completed on:',
                  self.data.num2date(order.executed.dt).strftime('%Y-%m-%d'))
            print('-- BUY Price:', order.executed.price)

    def next(self):
        self.callcounter += 1

        # For hilight
        week_color = colorama.Fore.YELLOW if len(self) % 2 else colorama.Fore.RED
        day_color = colorama.Fore.GREEN if self.callcounter % 4 in [1, 2] else colorama.Fore.BLUE

        txtfields = list()
        txtfields.append('%04d' % self.callcounter)
        txtfields.append(week_color + colorama.Style.BRIGHT + '%04d' % len(self))
        txtfields.append('%04d' % len(self.data0))
        txtfields.append(day_color + self.data.datetime.datetime(0).replace(microsecond=0).isoformat() + '  ')
        txtfields.append('%.2f' % self.data0.open[0])
        txtfields.append('%.2f' % self.data0.high[0])
        txtfields.append('%.2f' % self.data0.low[0])
        txtfields.append('%.2f' % self.data0.close[0])
        txtfields.append('%.2f' % self.data0.volume[0])
        txtfields.append('%.2f' % self.data0.openinterest[0])
        print(', '.join(txtfields))

        if not self.position:
            if len(self.data) > self.lcontrol:
                if self.data.high == self.highest:  # today is highest!!!
                    print('High %.2f >= Highest %.2f' %
                          (self.data.high[0], self.highest[0]))
                    print('LAST 19 highs:',
                          self.data.high.get(size=19, ago=-1))
                    print('-- BUY on date:',
                          self.data.datetime.date().strftime('%Y-%m-%d'))
                    ex = bt.Order.Market if self.p.market else bt.Order.Close
                    self.buy(exectype=ex)
                    self.inmarket = len(self)  # reset period in market

        else:  # in the market
            if (len(self) - self.inmarket) >= self.p.sellafter:
                self.sell()

        self.lcontrol = len(self.data)


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)
    # intra day consider a bar with the same time as the end of session to be the end of session
    cerebro.broker.set_eosbar(True)

    dkwargs = dict()
    if args.fromdate:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
        dkwargs['fromdate'] = fromdate

    if args.todate:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
        dkwargs['todate'] = todate

    datapath = '../datas/yhoo-1996-2015.txt'
    data = bt.feeds.YahooFinanceCSVData(dataname=datapath,
                                        timeframe=bt.TimeFrame.Days,
                                        compression=1,
                                        **dkwargs)
    data.addfilter(bt.filters.DaySplitter_Close)
    cerebro.replaydata(data, timeframe=bt.TimeFrame.Weeks, compression=1)

    cerebro.addstrategy(St,
                        sellafter=args.sellafter,
                        highperiod=args.highperiod,
                        market=args.market)

    cerebro.run(runonce=False, preload=False, oldbuysell=args.oldbuysell)
    if args.plot:
        pkwargs = dict(style='bar')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pinkfish challenge')

    parser.add_argument('--fromdate', required=False,
                        default='2005-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False,
                        default='2006-12-31',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store',
                        type=float, default=50000,
                        help=('Cash to start with'))

    parser.add_argument('--sellafter', required=False, action='store',
                        type=int, default=2,
                        help=('Sell after so many bars in market'))

    parser.add_argument('--highperiod', required=False, action='store',
                        type=int, default=20,
                        help=('Period to look for the highest'))

    parser.add_argument('--market', required=False, action='store_true',
                        help=('Use Market exec instead of Close'))

    parser.add_argument('--oldbuysell', required=False, action='store_true',
                        help=('Old buysell plot behavior - ON THE PRICE'))

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const=True,
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example (escape the quotes if needed):\n'
                              '\n'
                              '	 --plot style="candle" (to plot candles)\n'))

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == '__main__':
    colorama.init(autoreset=True)
    runstrat()
