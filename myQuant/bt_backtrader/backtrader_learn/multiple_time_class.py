import backtrader as bt
import datetime
from backtrader.dataseries import TimeFrame
import pandas as pd
import math


# rewrite strategy
class MultiStrategy(bt.Strategy):
    params = (
        ('period', 5),
    )
    # Set 4 different status for 4 situations
    Empty, M15Hold, H1Hold, D1Hold = range(4)
    States = [
        'Empty', 'M15Hold', 'H1Hold', 'D1Hold',
    ]

    def log(self, txt):
        dt = self.datas[0].datetime.datetime(0)
        print('%s,%s' % (dt.isoformat(), txt))

    # initiate fun
    def __init__(self):
        # Set 3 different Moving Average lines
        self.ma15m = bt.talib.SMA(self.dnames.hs15m, timeperiod=self.p.period)
        self.ma1h = bt.talib.SMA(self.dnames.hs1h, timeperiod=self.p.period)
        self.ma1d = bt.talib.SMA(self.dnames.hs1d, timeperiod=self.p.period)

        # 3 different cross-over indicators
        self.c15m = bt.indicators.CrossOver(
            self.dnames.hs15m, self.ma15m, plot=False
        )
        self.c1h = bt.indicators.CrossOver(
            self.dnames.hs1h, self.ma1h, plot=False
        )
        self.c1d = bt.indicators.CrossOver(
            self.dnames.hs1d, self.ma1d, plot=False
        )

        self.bsig15m = self.c15m == 1
        self.bsig1h = self.c1h == 1
        self.bsig1d = self.c1d == 1
        self.sell_signal = self.c1d == -1

        # function map to conduct different strategy in different status
        self.st = self.Empty
        self.st_map = {
            self.Empty: self._empty,
            self.M15Hold: self._m15hold,
            self.H1Hold: self._h1hold,
            self.D1Hold: self._d1hold
        }

        self.order = None
        # Indicator
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)

    # notify when order is executed
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, St: %s, Size: %d, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (
                        self.States[self.st],
                        order.executed.size,
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm
                    )
                )
            else:  # sell
                self.log(
                    'SELL EXECUTED, St: %s, Size: %d, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (
                        self.States[self.st],
                        order.executed.size,
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm
                    )
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    # notify when trade result
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(
            'OPERATION PROFIT, GROSS %.2f, NET %.2f' %
            (trade.pnl, trade.pnlcomm)
        )

    def next(self):
        if self.order:
            return
        self.order = self.st_map[self.st]()

        if self.position and not self.order:
            if self.sell_signal:
                self.st = self.Empty
                self.order = self.close()

    def _empty(self):
        if self.bsig15m:
            price = self.data0.close[0]
            cash = self.broker.get_cash()
            share = (0.2 * cash) / price
            self.st = self.M15Hold
            return self.buy(size=share)

    def _m15hold(self):
        if self.bsig1h:
            price = self.data0.close[0]
            cash = self.broker.get_cash()
            share = (0.5 * cash) / price
            self.st = self.H1Hold
            return self.buy(size=share)

    def _h1hold(self):
        if self.bsig1d:
            price = self.data0.close[0]
            cash = self.broker.get_cash()
            share = (0.5 * cash) / price
            self.st = self.H1Hold
            return self.buy(size=share)

    def _d1hold(self):
        return None
