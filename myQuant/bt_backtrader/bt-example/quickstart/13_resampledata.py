import backtrader as bt
import backtrader.indicators as btind
from backtrader_plotting import Bokeh
import inspect


class St(bt.Strategy):
    params = dict(multi=True)

    def __init__(self):
        self.pp = pp = btind.PivotPoint(self.data1)
        pp.plotinfo.plot = False  # 停用绘图
        if self.p.multi:
            pp1 = pp()  # 耦合整个指标
            self.sellsignal = self.data0.close < pp1.s1
        else:
            self.sellsignal = self.data0.close < pp.s1()

    def next(self):
        txt = ','.join(
            ['%04d' % len(self),
             '%04d' % len(self.data0),
             '%04d' % len(self.data1),
             self.data.datetime.date(0).isoformat(),
             '%.2f' % self.data0.close[0],
             '%.2f' % self.pp.s1[0],
             '%.2f' % self.sellsignal[0]])
        print(txt)


cerebro = bt.Cerebro()
datapath = '../datas/orcl-1995-2014.txt'

# Create a Data Feed
data = bt.feeds.YahooFinanceCSVData(
    dataname=datapath,
    # Do not pass values before this date
    fromdate=bt.datetime.datetime(2000, 1, 1),
    # Do not pass values before this date
    todate=bt.datetime.datetime(2000, 12, 31),
    # Do not pass values after this date
    reverse=False)
cerebro.adddata(data)
cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)
cerebro.broker.set_cash(1000000)
cerebro.addstrategy(St, multi=False)
cerebro.run()
cerebro.plot(style='bar', iplot=False)
# cerebro.plot(Bokeh(style='bar'))
