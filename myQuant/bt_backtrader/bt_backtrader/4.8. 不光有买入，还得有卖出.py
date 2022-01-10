import datetime  #
import os.path  # 路径管理
import sys  # 获取当前运行脚本的路径 (in argv[0])

# 导入backtrader框架
import backtrader as bt


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 保存收盘价的引用
        self.dataclose = self.datas[0].close
        # 跟踪挂单
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # broker 提交/接受了，买/卖订单则什么都不做
            return

        # 检查一个订单是否完成
        # 注意: 当资金不足时，broker会拒绝订单
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('已买入, %.2f' % order.executed.price)
            elif order.issell():
                self.log('已卖出, %.2f' % order.executed.price)

            # 记录当前交易数量
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        # 其他状态记录为：无挂起订单
        self.order = None

    def next(self):
        # 记录收盘价
        self.log('Close, %.2f' % self.dataclose[0])

        # 如果有订单正在挂起，不操作
        if self.order:
            return

        # 如果没有持仓则买入
        if not self.position:
            # 今天的收盘价 < 昨天收盘价
            if self.dataclose[0] < self.dataclose[-1]:
                # 昨天收盘价 < 前天的收盘价
                if self.dataclose[-1] < self.dataclose[-2]:
                    # 买入
                    self.log('买入, %.2f' % self.dataclose[0])
                    # 跟踪订单避免重复
                    self.order = self.buy()
        else:
            # 如果已经持仓，且当前交易数据量在买入后5个单位后
            if len(self) >= (self.bar_executed + 5):
                # 全部卖出
                self.log('卖出, %.2f' % self.dataclose[0])
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
    datapath = os.path.join(modpath, '../../datas/orcl-1995-2014.txt')

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

    # 设置投资金额100000.0
    cerebro.broker.setcash(100000.0)
    # 引擎运行前打印期出资金
    print('组合期初资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    # 引擎运行后打期末资金
    print('组合期末资金: %.2f' % cerebro.broker.getvalue())
