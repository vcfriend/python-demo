#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   get_all_trades.py
@Time    :   2021/02/24 19:59:48
@Author  :   Jeffrey Wang
@Version :   1.0
@Contact :   shwangjj@163.com
@Desc    :   读取已经发生过的所有Trade

逻辑：
1. 第一天，下单买100股，卖50股
2. 第二天，昨日单执行，Trade1建立，然后再下50股卖单
3. 第三天，昨日卖单执行，Trade1结束。再下100股卖单
4. 第四天，昨日卖单执行，Trade2建立，再下100股买单
5. 第五天，昨日买单执行，Trade2结束
6. 第六天，输出所有Trade

输出：
1. 控制台输出
初始账户价值: 200000.00
2019-01-03, 买单执行, 5.63
2019-01-03, 卖单执行, 5.63
2019-01-03, Trade id = 1 (size=100)
2019-01-04, 卖单执行, 5.64
2019-01-04, Trade id = 1 (size=0)
2019-01-04, 毛收益 0.50
2019-01-07, 买单执行, 5.8
2019-01-07, Trade id = 2 (size=100)
最终账户价值: 199993.50


'''
import backtrader as bt
import thinkinbt.p1.data_tl as data_tl


# 策略
class DemoStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.order = None  # 未决订单

    def next(self):
        # 如果有未决订单则什么都不做
        if self.order:
            self.log("存在未决订单")
            return

        days = len(self.data)
        if days == 1:
            # 第1天 20190102
            self.order = self.buy(size=100)
            self.order = self.sell(size=50)
        elif days == 2:
            # 第2天 20190103
            self.order = self.sell(size=50)
            # self.log(self._trades[self.data0][0][0])
        elif days == 3:
            # 第3天 20190104
            self.order = self.sell(size=100)
        elif days == 4:
            # 第4天 20190105
            self.order = self.buy(size=100)

    def stop(self):
        # 输出所有的Trade：
        self.log("所有的交易")
        for t in self._trades[self.data][0]:  # tradeid=0的所有交易
            self.log(t.ref)
            print(t)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("买单执行, {p}".format(p=order.executed.price))
            elif order.issell():
                self.log("卖单执行, {p}".format(p=order.executed.price))

        self.order = None  # 重置未决订单

    def notify_trade(self, trade):
        self.log("Trade id = {0} (size={1})".format(trade.ref, trade.size))
        if trade.isclosed:
            self.log("毛收益 %0.2f" % trade.pnl)


# 启动回测
def engine_run():
    # 初始化引擎
    cerebro = bt.Cerebro()
    # 给Cebro引擎添加策略
    cerebro.addstrategy(DemoStrategy)
    # 设置初始资金：
    cerebro.broker.setcash(200000.0)
    # 从csv文件加载数据
    data = data_tl.get_stock_daily(stock_id="600016.SH", start="20190101", end="20190115")
    cerebro.adddata(data, name="民生银行")
    # 回测启动运行
    print('初始账户价值: %.2f' % cerebro.broker.getvalue())
    # 回测启动运行
    cerebro.run()
    print('最终账户价值: %.2f' % cerebro.broker.getvalue())
    # cerebro.plot()


if __name__ == '__main__':
    engine_run()
