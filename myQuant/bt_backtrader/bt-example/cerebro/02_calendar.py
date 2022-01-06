from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import colorama

import backtrader as bt


class NYSE_2016(bt.TradingCalendar):
    params = dict(
        holidays=[
            datetime.date(2016, 1, 1),
            datetime.date(2016, 1, 18),
            datetime.date(2016, 2, 15),
            datetime.date(2016, 3, 25),
            datetime.date(2016, 5, 30),
            datetime.date(2016, 7, 4),
            datetime.date(2016, 9, 5),
            datetime.date(2016, 11, 24),
            datetime.date(2016, 12, 26),
        ]
    )


class St(bt.Strategy):
    params = dict(
    )

    def __init__(self):
        pass

    def start(self):
        self.t0 = datetime.datetime.utcnow()

    def stop(self):
        t1 = datetime.datetime.utcnow()
        print('Duration:', t1 - self.t0)

    def prenext(self):
        self.next()

    def next(self):
        print('Strategy len {} datetime {}'.format(
            len(self), self.datetime.date()), end=' ')

        print(colorama.Fore.GREEN + 'Data0 len {} datetime {}'.format(
            len(self.data0), self.data0.datetime.date()) + colorama.Fore.RESET, end=' ')

        if len(self.data1):
            print(colorama.Fore.YELLOW + 'Data1 len {} datetime {}'.format(
                len(self.data1), self.data1.datetime.date()) + colorama.Fore.RESET)
        else:
            print()


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    # Data feed
    data = bt.feeds.GenericCSVData(dataname='../datas/GOOG_D1.csv', dtformat='%Y-%m-%d', openinterest=-1, **kwargs)

    cerebro.adddata(data)

    d1 = cerebro.resampledata(data,
                              timeframe=getattr(bt.TimeFrame, args.timeframe))
    d1.plotinfo.plotmaster = data
    d1.plotinfo.sameaxis = True

    if args.pandascal:
        cerebro.addcalendar(args.pandascal)
    elif args.owncal:
        cerebro.addcalendar(NYSE_2016)

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')'))

    # Sizer
    cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Trading Calendar Sample'
        )
    )

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='2016-01-01',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='2016-12-31',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    pgroup = parser.add_mutually_exclusive_group(required=False)
    pgroup.add_argument('--pandascal', required=False, action='store',
                        default='', help='Name of trading calendar to use')

    pgroup.add_argument('--owncal', required=False, action='store_true',
                        help='Apply custom NYSE 2016 calendar')

    parser.add_argument('--timeframe', required=False, action='store',
                        default='Weeks', choices=['Weeks', 'Months', 'Years'],
                        help='Timeframe to resample to')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
