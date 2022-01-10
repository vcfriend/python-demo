"""
SimpleStrategy.py就是动量+趋势跟踪的策略，策略思路为：计算24只股票过去30日的收益率并进行排序，
选择前10只股票加入选股池（动量），逐日滚动计算和判断：如果选股池中某只个股满足股价位于20均线以上且没有持仓时买入
（以20日均线为生命线跟踪趋势）；如果某只个股已持仓但判断不在选股池中或股价位于20均线以下则卖出。每次交易根据十只个股平均持仓。
这个是从网上找的一个现成策略，我随便找了10只股票，并不完全满足策略要求，主要为了测试backtrader是否为我所用了，具体的策略问题等以后慢慢研究。
"""

import backtrader as bt


class SimpleStrategy(bt.Strategy):
    # 策略参数
    params = dict(
        period=20,  # 均线周期
        look_back_days=30,
        printlog=False
    )

    def __init__(self):
        self.mas = dict()
        # 遍历所有股票,计算20日均线
        for data in self.datas:
            self.mas[data._name] = bt.ind.SMA(data.close, period=self.p.period)

    def next(self):
        # 计算截面收益率
        rate_list = []
        for data in self.datas:
            if len(data) > self.p.look_back_days:
                p0 = data.close[0]
                pn = data.close[-self.p.look_back_days]
                rate = (p0 - pn) / pn
                rate_list.append([data._name, rate])
        # 股票池
        long_list = []
        sorted_rate = sorted(rate_list, key=lambda x: x[1], reverse=True)
        long_list = [i[0] for i in sorted_rate[:10]]
        # 得到当前的账户价值
        total_value = self.broker.getvalue()
        p_value = total_value * 0.9 / 10
        for data in self.datas:
            # 获取仓位
            pos = self.getposition(data).size
            if not pos and data._name in long_list and \
                    self.mas[data._name][0] > data.close[0]:
                size = int(p_value / 100 / data.close[0]) * 100
                self.buy(data=data, size=size)
            if pos != 0 and data._name not in long_list or \
                    self.mas[data._name][0] < data.close[0]:
                self.close(data=data)

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()},{txt}')

    # 记录交易执行情况（可省略，默认不输出结果）
    def notify_order(self, order):
        # 如果order为submitted/accepted,返回空
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 如果order为buy/sell executed,报告价格结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入:\n价格:{order.executed.price:.2f},\
                成本:{order.executed.value:.2f},\
                手续费:{order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'卖出:\n价格：{order.executed.price:.2f},\
                成本: {order.executed.value:.2f},\
                手续费{order.executed.comm:.2f}')
            self.bar_executed = len(self)
        # 如果指令取消/交易失败, 报告结果
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('交易失败')
        self.order = None

    # 记录交易收益情况（可省略，默认不输出结果）
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'策略收益：\n毛收益 {trade.pnl:.2f}, 净收益 {trade.pnlcomm:.2f}')
