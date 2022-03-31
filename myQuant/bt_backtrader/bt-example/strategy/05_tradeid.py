from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import itertools

# 以上可以发送到一个独立的模块
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind

from observers.mtradeobserver import MTradeObserver


class MultiTradeStrategy(bt.Strategy):
    """该策略在收盘价向上向下穿过简单移动平均线时买入。
    通过将参数“onlylong”设置为True，它可以是一个只做多的策略
    """
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

        # 在第二个数据上创建 SMA
        sma = btind.MovAv.SMA(self.data, period=self.p.period)
        # 从关闭移动平均线创建交叉信号
        self.signal = btind.CrossOver(self.data.close, sma)

        # 在不同的贸易之间交替
        if self.p.mtrade:
            self.tradeid = itertools.cycle([0, 1, 2])
        else:
            self.tradeid = itertools.cycle([0])

    def next(self):
        if self.order:
            return  # 如果订单处于活动状态，则不允许新订单

        if self.signal > 0.0:  # 向上交叉
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
            return  # 等待进一步通知

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
        # 不要在此日期之前传递值
        #         fromdate=datetime.datetime(2000, 1, 1),
        # 不要在此日期之前传递值
        #         todate=datetime.datetime(2000, 12, 31),
        # 在此日期之后不要传递值
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
