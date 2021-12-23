from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime
import backtrader as bt
import pandas as pd
import tushare as ts
import os

# 使用tushare 从网络加载数据源
def get_tushare_online_daily_data(
        code="000001.SZ",
        date_start="20190101",
        date_end="20191231",
        format="%Y%m%d", ):
    """使用 tushare 加载 数据返回BT Data
    """
    # %Y%m%d 日期格式的字符串
    dt_start = datetime.datetime.strptime(date_start, format).strftime("%Y%m%d")
    dt_end = datetime.datetime.strptime(date_end, format).strftime("%Y%m%d")
    # TOKEN = '341d66d4586929fa56f3f987e6c0d5bd23fb2a88f5a48b83904d134b'
    TOKEN = 'cd9e075edc5e5106a21a9c38b42a4e92744e08e91405c977e52e69ff'

    ts.set_token(TOKEN)
    pro = ts.pro_api()

    try:
        # 加载数据
        df = pro.daily(ts_code=code, start_date=dt_start, end_date=dt_end)
        df.sort_values(by=["trade_date"], ascending=True,
                       inplace=True)  # 按日期先后排序
        df.reset_index(inplace=True, drop=True)

        # 开始数据清洗：
        # 按日期先后排序
        df.sort_values(by=["trade_date"], ascending=True, inplace=True)
        # 将日期列，设置成index
        df.index = pd.to_datetime(df.trade_date, format='%Y%m%d')
        # 增加一列openinterest
        df['openinterest'] = 0.00
        # 取出特定的列
        df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']]
        # 列名修改成指定的
        df.rename(columns={"vol": "volume"}, inplace=True)

        print(df.shape[0])
        # print(df.info())
        print(df.head())
        # 使用pandas数据源创建交易数据集
        data = bt.feeds.PandasData(dataname=df)

        return data
    except Exception as err:
        print("下载{0}完毕失败！")
        print("失败原因 = " + str(err))

class TestSizer(bt.Sizer):
    params = (('stake', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            return self.p.stake
        position = self.broker.getposition(data)
        if not position.size:
            return 0
        else:
            return position.size
        return self.p.stake


class TestStrategy(bt.Strategy):
    params = (('maperiod', 15), ('printlog', False),)

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        self.order = None
        self.buyprice = 0
        self.buycomm = 0
        self.newstake = 0
        self.buytime = 0
        # 参数计算，唐奇安通道上轨、唐奇安通道下轨、ATR
        self.DonchianHi = bt.indicators.Highest(self.datahigh(-1), period=20, subplot=False)
        self.DonchianLo = bt.indicators.Lowest(self.datalow(-1), period=10, subplot=False)
        self.TR = bt.indicators.Max((self.datahigh(0) - self.datalow(0)), abs(self.dataclose(-1) - self.datahigh(0)),
                                    abs(self.dataclose(-1) - self.datalow(0)))
        self.ATR = bt.indicators.SimpleMovingAverage(self.TR, period=14, subplot=True)
        # 唐奇安通道上轨突破、唐奇安通道下轨突破
        self.CrossoverHi = bt.ind.CrossOver(self.dataclose(0), self.DonchianHi)
        self.CrossoverLo = bt.ind.CrossOver(self.dataclose(0), self.DonchianLo)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm), doprint=True)
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm), doprint=True)
                self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))

    def next(self):
        if self.order:
            return
            # 入场
        if self.CrossoverHi > 0 and self.buytime == 0:
            self.newstake = self.broker.getvalue() * 0.01 / self.ATR
            self.newstake = int(self.newstake / 100) * 100
            self.sizer.p.stake = self.newstake
            self.buytime = 1
            self.order = self.buy()
            # 加仓
        elif self.datas[0].close > self.buyprice + 0.5 * self.ATR[0] and self.buytime > 0 and self.buytime < 5:
            self.newstake = self.broker.getvalue() * 0.01 / self.ATR
            self.newstake = int(self.newstake / 100) * 100
            self.sizer.p.stake = self.newstake
            self.order = self.buy()
            self.buytime = self.buytime + 1
            # 出场
        elif self.CrossoverLo < 0 and self.buytime > 0:
            self.order = self.sell()
            self.buytime = 0
            # 止损
        elif self.datas[0].close < (self.buyprice - 2 * self.ATR[0]) and self.buytime > 0:
            self.order = self.sell()
            self.buytime = 0

    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' % (self.params.maperiod, self.broker.getvalue()), doprint=True)


if __name__ == '__main__':
    # 创建主控制器    
    cerebro = bt.Cerebro()
    # 加入策略    
    cerebro.addstrategy(TestStrategy)
    # 准备股票日线数据，输入到backtrader    
    file_path = os.path.join('./fd_data/600016.SH.csv')
    df = pd.read_csv(file_path,nrows=500, index_col=0, parse_dates=True)
    # 按日期先后排序
    df.sort_values(by=["trade_date"], ascending=True, inplace=True)
    # 将日期列，设置成index
    df.index = pd.to_datetime(df.trade_date, format='%Y%m%d')
    df['openinterest'] = 0
    print('df:',df.info())
    print(df.head())
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    # broker设置资金、手续费    
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)
    # 设置买入策略    
    cerebro.addsizer(TestSizer)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 启动回测    
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 曲线绘图输出    
    cerebro.plot()
