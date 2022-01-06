import backtrader as bt
import math
import datatime


# define strategy
class VIXStrategy(bt.Strategy):
    def __init__(self):
        self.vix = self.dnames['VIXdata'].vix
        self.price = self.dnames['stock_data'].close

    def log(self, txt):
        dt = self.datas[0].datetime.datetime(0)
        print('%s,%s' % (dt.isoformat(), txt))

    def next(self):
        size = int(math.floor(self.broker.get_cash() / self.price[0]))
        if self.vix[0] > 35 and not self.position:
            self.buy(size=size)
        if self.vix[0] < 10 and self.position.size > 0:
            self.sell(size=self.position.size)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Size: %d, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.size, order.executed.price, order.executed.value, order.executed.comm)
                )
            else:  # sell
                self.log(
                    'SELL EXECUTED, Size: %d, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.size, order.executed.price, order.executed.value, order.executed.comm)
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')


# define feeding data
class stock_data(bt.feeds.GenericCSVData):
    lines = ('vix',)
    params = (
        ('dtformat', '%Y-%m-%d'),
        ('date', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 6),
        ('openinterest', -1),
        ('vix', 9),
    )


class VIXdata(bt.feeds.GenericCSVData):
    lines = ('vix',)
    params = (
        ('dtformat', '%Y-%m-%d'),
        ('date', 0),
        ('vix', 4),
        ('volume', -1),
        ('openinterest', -1),
    )


cerebro = bt.Cerebro()
cerebro.broker.setcash(100000)
# construct running code
stock_data_file = 'data//stock_data.csv'
vix_file = 'data//vix.csv'

stock_data_feed = stock_data(dataname=stock_data_file)
vix_feed = VIXdata(dataname=vix_file)

cerebro.adddata(stock_data_feed, name='stock_data')
cerebro.adddata(vix_feed, name='VIXdata')

cerebro.addstrategy(VIXStrategy)

cerebro.run()
cerebro.plot(volume=False)
