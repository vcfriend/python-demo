# %%
import backtrader as bt
from backtrader.dataseries import TimeFrame
import math


class MACD_Strategy(bt.Strategy):
    params = (
        ('fast_period', 100),
        ('slow_period', 240),
    )

    def __init__(self):
        # Set different Moving Average lines
        self.fast_ema = bt.ind.EMA(
            self.data.close, period=self.params.fast_period, plotname='fast EMA'
        )
        self.slow_ema = bt.ind.EMA(
            self.data.close, period=self.params.slow_period, plotname='slow EMA'
        )

        # MACD cross-over indicators
        self.crossover = bt.indicators.CrossOver(
            self.fast_ema, self.slow_ema
            # plot=False
        )

    def log(self, txt):
        dt = self.datas[0].datetime.datetime(0)
        print('%s,%s' % (dt.isoformat(), txt))

    def next(self):
        if self.position.size == 0:
            if self.crossover > 0:
                self.size = math.floor(self.broker.cash * 0.95 / self.data.close)

                # print('buy {} share of ETH at {}'.format(self.size, self.data.close[0]))

                self.buy(size=self.size)

        if self.position.size > 0:
            if self.crossover < 0:
                self.size = math.floor(self.broker.cash * 0.95 / self.data.close)

                # print('sell {} share of ETH at {}'.format(self.size, self.data.close[0]))

                self.close()

    # def notify_order(self,order):
    #     if order.status in [order.Submitted, order.Accepted]:
    #         return

    #     if order.status == order.Completed:
    #         if order.isbuy():
    #             self.log(
    #                 'BUY EXECUTED, Size: %d, Price: %.2f, Cost: %.2f, Comm %.2f' %
    #                 (order.executed.size,order.executed.price,order.executed.value,order.executed.comm)
    #             )
    #         else: # sell
    #             self.log(
    #                 'SELL EXECUTED, Size: %d, Price: %.2f, Cost: %.2f, Comm %.2f' %
    #                (order.executed.size,order.executed.price,order.executed.value,order.executed.comm)
    #             )

    #     elif order.status in [order.Canceled,order.Margin,order.Rejected]:
    #         self.log('Order Canceled/Margin/Rejected')


cerebro = bt.Cerebro()
data = bt.feeds.GenericCSVData(
    dataname='E://Quant//Learn backtrader//data//15min.csv',
    timeframe=bt.TimeFrame.Minutes,
    dtformat='%Y-%m-%d %H:%M:%S',
    datetime=0,
    open=1,
    high=2,
    low=3,
    close=4,
    volume=5,
    openinteres=-1,
)
cerebro.adddata(data)
# cerebro.addobserver(bt.observers.Trades)
# cerebro.addobserver(bt.observers.BuySell)

cerebro.addstrategy(MACD_Strategy)

cerebro.broker.setcash(100000000)

cerebro.broker.setcommission(0.002)

back = cerebro.run()
# %%
print(cerebro.broker.getvalue())
# %%
