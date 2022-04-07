import os
import backtrader as bt
import argparse


def runstrat(args=None):
    args = parse_args(args)
    dkwargs = dict()

    file_path = "datas\\SQRB13-5m-20180102-20220330.csv"
    dt_start, dt_end = '20180702', '20180703'
    dt_datetime_format = '%Y%m%d%H%M%S'
    dt_date_format = '%Y%m%d'

    if args.dtformat is not None:
        dt_datetime_format = args.dtformat
        dt_date_format = dt_datetime_format[:dt_datetime_format.find('%d') + len('%d')]
    if args.fromdate is not None:
        dt_start = bt.datetime.datetime.strptime(args.fromdate, dt_date_format)
    if args.todate is not None:
        dt_end = bt.datetime.datetime.strptime(args.todate, dt_date_format)
    if args.data is not None:
        file_path = args.data

    myQuant_ROOT = os.getcwd()[:os.getcwd().find("bt_backtrader\\") + len("bt_backtrader\\")]  # 获取项目中相对根路径
    file_path = os.path.join(myQuant_ROOT, file_path)  #文件路径
    print(file_path)
    if not os.path.exists(file_path):
        print("数据源文件未找到！" + file_path)
        raise Exception("数据源文件未找到！" + file_path)

    dkwargs['fromdate'] = dt_start
    dkwargs['todate'] = dt_end
    dkwargs['dtformat'] = dt_datetime_format

    # 加载数据
    data = bt.feeds.GenericCSVData(dataname=file_path, **dkwargs)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    # 设置投资金额100000.0
    cerebro.broker.setcash(100000.0)

    cerebro.broker.setcommission(
        # 交易手续费，根据margin取值情况区分是百分比手续费还是固定手续费
        commission=0.005,
        # 期货保证金，决定着交易费用的类型,只有在stocklike=False时起作用
        margin=13,
        # 乘数，盈亏会按该乘数进行放大
        mult=10.0,
        # 交易费用计算方式，取值有：
        # 1.CommInfoBase.COMM_PERC 百分比费用
        # 2.CommInfoBase.COMM_FIXED 固定费用
        # 3.None 根据 margin 取值来确定类型
        commtype=None,
        # 当交易费用处于百分比模式下时，commission 是否为 % 形式
        # True，表示不以 % 为单位，0.XX 形式；False，表示以 % 为单位，XX% 形式
        percabs=True,
        # 是否为股票模式，该模式通常由margin和commtype参数决定
        # margin=None或COMM_PERC模式时，就会stocklike=True，对应股票手续费；
        # margin设置了取值或COMM_FIXED模式时,就会stocklike=False，对应期货手续费
        stocklike=False,
        # 计算持有的空头头寸的年化利息
        # days * price * abs(size) * (interest / 365)
        interest=0.0,
        # 计算持有的多头头寸的年化利息
        interest_long=False,
        # 杠杆比率，交易时按该杠杆调整所需现金
        leverage=1.0,
        # 自动计算保证金
        # 如果False, 则通过margin参数确定保证金
        # 如果automargin<0, 通过mult*price确定保证金
        # 如果automargin>0, 如果automargin*price确定保证金
        automargin=False,
        # 交易费用设置作用的数据集(也就是作用的标的)
        # 如果取值为None，则默认作用于所有数据集(也就是作用于所有assets)
        name=None
    )

    # strategy
    cerebro.addstrategy(TestStrategy)

    # 引擎运行前打印期出资金
    print('组合期初资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    # 引擎运行后打期末资金
    print('组合期末资金: %.2f' % cerebro.broker.getvalue())

    if args.plot:
        pkwargs = dict(style='bar')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for Order Target')

    parser.add_argument('--data', required=False,
                        default="datas\\SQRB13-5m-20180102-20220330.csv",
                        help='Specific data to be read in')
    parser.add_argument('--dtformat', required=False, default='%Y%m%d%H%M%S',
                        help='Ending date in data datetime format')
    parser.add_argument('--fromdate', required=False, default='20180702',
                        help='Starting date in `dtformat` format')
    parser.add_argument('--todate', required=False, default='20180715',
                        help='Ending date in `dtformat` format')
    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const=True, default='style="bar"',
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example:\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))
    parser.add_argument("-f", "--file", default="file")  # 接收这个-f参数
    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.strftime('%Y-%m-%d %H:%M:%S'), txt))

    def __init__(self):
        self.myentryprice = 0.0  # 入场价格
        self.myexitprice = 0.0  # 离场价格

        # 建立对于DataFeed的Open/Close价格的引用参数
        self.dtopen = self.datas[0].open
        self.dtclose = self.datas[0].close
        self.dthigh = self.datas[0].high
        self.dtlow = self.datas[0].low
        # 跟踪挂单
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # broker 提交/接受了，买/卖订单则什么都不做
            return
        t = ''
        # 检查一个订单是否完成
        # 注意: 当资金不足时，broker会拒绝订单
        if order.status in [order.Completed]:
            if order.isbuy():
                t += '+++++++++已买入{:+d}, {:.2f}'.format(self.position.size, order.executed.price)
            elif order.issell():
                t += '---------已卖出{:+d}, {:.2f}'.format(self.position.size, order.executed.price)
            # 记录当前交易数量
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            t += ' 订单取消/保证金不足/拒绝'

        t += ' 资产{:.2f}'.format(self.broker.getvalue())
        self.log(t)
        # 其他状态记录为：无挂起订单
        self.order = None

    def next(self):
        # 记录收盘价
        # self.log('Close, %.2f' % self.close[0])

        # 如果有订单正在挂起，不操作
        if self.order:
            return
        percent = 5 / 100.0
        self.order = self.order_target_percent(target=percent)  # 百分比开仓
        t = ''
        t += ' 资产{:.2f}'.format(self.broker.getvalue())
        # 如果没有持仓则买入
        if not self.position:
            # 今天的收盘价 > 昨天收盘价
            if self.dtclose[0] > self.dtopen[0]:
                # 买入
                self.log('买入, %.2f' % self.dtclose[0] + t)
                self.myentryprice = self.dtclose[0]  # 记录入场价
                # 跟踪订单避免重复
                self.order = self.buy()
                # 今天的收盘价 < 昨天收盘价
            if self.dtclose[0] < self.dtopen[0]:
                # 买入
                self.log('卖出, %.2f' % self.dtclose[0] + t)
                self.myentryprice = self.dtclose[0]  # 记录入场价
                # 跟踪订单避免重复
                self.order = self.sell()

        else:
            # 如果已经持仓，且当前交易数据量在买入后5个单位后
            if len(self) >= (self.bar_executed + 5):
                # 全部卖出
                self.log('平仓, %.2f' % self.dtclose[0] + t)
                # 跟踪订单避免重复
                self.order = self.close()


if __name__ == '__main__':
    runstrat()
