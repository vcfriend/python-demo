import datetime  #
import os.path  # 路径管理
import sys  # 获取当前运行脚本的路径 (in argv[0])

# 导入backtrader框架
import backtrader as bt


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):
    params = (
        # 均线参数设置15天，15日均线
        ('maperiod', 15),
    )

    def log(self, txt, dt=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 保存收盘价的引用
        self.dataclose = self.datas[0].close
        # 跟踪挂单
        self.order = None
        # 买入价格和手续费
        self.buyprice = None
        self.buycomm = None
        # 加入均线指标
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)  # 简单移动平均

        # 绘制图形时候用到的指标
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)  # 指数移动平均线
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=True)  # 加权移动平均线
        bt.indicators.StochasticSlow(self.datas[0])  # 随机慢
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)  # 平滑移动平均线
        bt.indicators.ATR(self.datas[0], plot=False)

    # 订单状态通知，买入卖出都是下单
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # broker 提交/接受了，买/卖订单则什么都不做
            return

        # 检查一个订单是否完成
        # 注意: 当资金不足时，broker会拒绝订单
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    '已买入, 价格: %.2f, 费用: %.2f, 佣金 %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log('已卖出, 价格: %.2f, 费用: %.2f, 佣金 %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            # 记录当前交易数量
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        # 其他状态记录为：无挂起订单
        self.order = None

    # 交易状态通知，一买一卖算交易
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('交易利润, 毛利润 %.2f, 净利润 %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # 记录收盘价
        self.log('Close, %.2f' % self.dataclose[0])

        # 如果有订单正在挂起，不操作
        if self.order:
            return

        # 如果没有持仓则买入
        if not self.position:
            # 今天的收盘价在均线价格之上
            if self.dataclose[0] > self.sma[0]:
                # 买入
                self.log('买入单, %.2f' % self.dataclose[0])
                # 跟踪订单避免重复
                self.order = self.buy()
        else:
            # 如果已经持仓，收盘价在均线价格之下
            if self.dataclose[0] < self.sma[0]:
                # 全部卖出
                self.log('卖出单, %.2f' % self.dataclose[0])
                # 跟踪订单避免重复
                self.order = self.sell()


if __name__ == '__main__':
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()
    # Cerebro引擎在后台创建broker(经纪人)，系统默认资金量为10000

    # 为Cerebro引擎添加策略
    cerebro.addstrategy(TestStrategy)

    # 获取当前运行脚本所在目录
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    # 拼接加载路径
    datapath = os.path.join('', '../../datas/orcl-1995-2014.txt')

    # 创建交易数据集
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # 数据必须大于fromdate
        fromdate=datetime.datetime(2000, 1, 1),
        # 数据必须小于todate
        todate=datetime.datetime(2000, 12, 31),
        reverse=False)

    # 加载交易数据
    cerebro.adddata(data)

    # 设置投资金额1000.0
    cerebro.broker.setcash(1000.0)

    # 每笔交易使用固定交易量
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    # 设置佣金为0.0
    cerebro.broker.setcommission(commission=0.0)

    # 引擎运行前打印期出资金
    print('组合期初资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    # 引擎运行后打期末资金
    print('组合期末资金: %.2f' % cerebro.broker.getvalue())

    # 绘制图像
    cerebro.plot()
