import os
import backtrader as bt
import argparse
import pandas as pd
import numpy as np


def runstrat(args=None):
    args = parse_args(args)
    dkwargs = dict()

    file_path = "datas\\SQRB13-5m-20180102-20220330.csv"
    dt_start, dt_end = '20180702', '20180703'
    dt_dtformat = '%Y%m%d%H%M%S'
    dt_date_format = '%Y%m%d'
    dt_tmformat = 'H%M%S'
    if args.dtformat is not None:
        dt_dtformat = args.dtformat
        dt_date_format = dt_dtformat[:dt_dtformat.find('%H')]
        dt_tmformat = dt_dtformat[dt_dtformat.find('%H'):]
    if args.fromdate is not None:
        dt_start = bt.datetime.datetime.strptime(args.fromdate, dt_date_format)
    if args.todate is not None:
        dt_end = bt.datetime.datetime.strptime(args.todate, dt_date_format)
    if args.data is not None:
        file_path = args.data

    myQuant_ROOT = os.getcwd()[:os.getcwd().find("bt_backtrader\\") + len("bt_backtrader\\")]  # 获取项目中相对根路径
    file_path = os.path.join(myQuant_ROOT, file_path)  # 文件路径
    print(file_path)
    if not os.path.exists(file_path):
        print("数据源文件未找到！" + file_path)
        raise Exception("数据源文件未找到！" + file_path)

    dkwargs['fromdate'] = dt_start
    dkwargs['todate'] = dt_end
    dkwargs['dtformat'] = dt_dtformat
    # dkwargs['tmformat'] = dt_tmformat

    print(dkwargs)
    # 加载数据
    df = pd.read_csv(filepath_or_buffer=file_path, )
    # 按日期先后排序
    df.sort_values(by=["datetime"], ascending=True, inplace=True)
    # 将日期列，设置成index
    df.index = pd.to_datetime(df.datetime, format=dt_dtformat)
    # 截取时间段内样本数据
    df = df[dt_start:dt_end]
    # 增加一列openinterest
    df['openinterest'] = 0.00
    # 取出特定的列
    df = df[['open', 'high', 'low', 'close', 'volume']]
    # 列名修改成指定的
    df.rename(columns={"volume": "vol"}, inplace=True)

    # data = bt.feeds.GenericCSVData(dataname=file_path, **dkwargs)
    # 使用pandas数据源创建交易数据集
    data = bt.feeds.PandasData(dataname=df, fromdate=dt_start, todate=dt_end)
    cerebro = bt.Cerebro(stdstats=False)
    # 观测器
    cerebro.addobserver(bt.observers.Broker)
    # cerebro.addobserver(bt.observers.Trades)
    # cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.DrawDown)
    # cerebro.addobserver(bt.observers.TimeReturn)
    # 添加分析指标
    # 返回年初至年末的年度收益率
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn')
    # 计算最大回撤相关指标
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown')
    # 计算年化收益：日度收益
    cerebro.addanalyzer(bt.analyzers.Returns, _name='_Returns', tann=252)
    # 计算年化夏普比率：日度收益
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio',
                        timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0)  # 计算夏普比率
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='_SharpeRatio_A')
    # 返回收益率时序
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')

    cerebro.adddata(data)
    # 设置投资金额100000.0
    cerebro.broker.setcash(100000.0)

    cerebro.broker.setcommission(
        # 交易手续费，根据margin取值情况区分是百分比手续费还是固定手续费
        # commission=0.0015,
        commission=2.4,
        # 期货保证金，决定着交易费用的类型,只有在stocklike=False时起作用
        margin=0,
        # 乘数，盈亏会按该乘数进行放大
        mult=10.0,
        # 交易费用计算方式，取值有：
        # 1.CommInfoBase.COMM_PERC 百分比费用
        # 2.CommInfoBase.COMM_FIXED 固定费用
        # 3.None 根据 margin 取值来确定类型
        commtype=bt.CommInfoBase.COMM_FIXED,
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
        # 如果 False, 则通过margin参数确定保证金
        # 如果automargin<0, 通过mult*price确定保证金
        # 如果automargin>0, 如果automargin*price确定保证金
        automargin=10 * 0.10,
        # 交易费用设置作用的数据集(也就是作用的标的)
        # 如果取值为None，则默认作用于所有数据集(也就是作用于所有assets)
        name=None
    )

    # strategy
    cerebro.addstrategy(TestStrategy)

    # 引擎运行前打印期出资金
    print('组合期初资金: %.2f' % cerebro.broker.getvalue())
    # 启动回测
    result = cerebro.run()
    # 引擎运行后打期末资金
    print('组合期末资金: %.2f' % cerebro.broker.getvalue())
    # 提取结果
    print("--------------- 年度收益率 -----------------")
    print(result[0].analyzers._AnnualReturn.get_analysis())
    print("--------------- 最大回撤 -----------------")
    print(result[0].analyzers._DrawDown.get_analysis())
    print("--------------- 年化收益：日度收益 -----------------")
    print(result[0].analyzers._Returns.get_analysis())
    print("--------------- 年化夏普比率：日度收益 -----------------")
    print(result[0].analyzers._SharpeRatio.get_analysis())
    print("--------------- SharpeRatio_A -----------------")
    print(result[0].analyzers._SharpeRatio_A.get_analysis())

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
                        default="datas\\DQC13-5m-20120709-20220330.csv",
                        help='Specific data to be read in')
    parser.add_argument('--dtformat', required=False, default='%Y%m%d%H%M%S',
                        help='Ending date in data datetime format')
    parser.add_argument('--fromdate', required=False, default='20120101',
                        help='Starting date in `dtformat` format')
    parser.add_argument('--todate', required=False, default='20130301',
                        help='Ending date in `dtformat` format')
    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const=True,
                        # default='style="bar"',
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example:\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))
    parser.add_argument("-f", "--file", default="file")  # 接收这个-f参数
    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


from enum import Enum


class UseTarget(Enum):
    """枚举开仓类型"""
    USE_TARGET_SIZE = 0  # 成交量
    USE_TARGET_VALUE = 1  # 目标金额
    USE_TARGET_PERCENT = 2  # 百分比


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.strftime('%a %Y-%m-%d %H:%M:%S'), txt))
        # 时间断点调试,调试条件 self.datas[0].datetime.datetime(0) >= bt.datetime.datetime.strptime('2018-01-23 14:05:00','%Y-%m-%d %H:%M:%S')
        # print('%s, %s' % (dt.isoformat(), txt))

    params = dict(

        RPP=1,  # 盈利千分比
        SPP=19,  # 亏损千分比
        RSPP=5,  # 盈亏千分比
        POSKK=10,  # 入场开仓单位 按(数量,金额,百分比)下单
        POSADP=10,  # 加减仓幅度百分比
        POSMAX=100,  # 最大开仓单位
        OCJK=1,  # CLOSE与OPEN的间隔
        SSPP=0,  # 最大回撤千分比
        addLongOrShort=0,  # 加仓方向addLongOrShort=0无限制,>0时只有多头加仓,<0时只有空头加仓
        valid=None,  # 订单生效时间

        use_target=UseTarget.USE_TARGET_PERCENT,  # use_target_percent 按目标百分比下单 use_target_size=False,  # 按目标数量下单 use_target_value=False,  # 按目标金额下单
    )

    def __init__(self):
        self.mprs = self.p.RSPP / 1000  # 盈亏千分比
        self.mpr = self.p.RPP / 1000  # 盈利千分比
        self.mps = self.p.SPP / 1000  # 亏损千分比
        self.mpposad = self.p.POSADP / 100  # 加减仓幅度百分比
        self.mposkk = self.p.POSKK  # 开仓单位
        self.mpposmin = self.p.POSKK  # 最小开仓单位
        self.mpposmax = self.p.POSMAX  # 最大开仓单位
        self.myentryprice_begin = 0.0  # 初始入场价格
        self.myentryprice = 0.0  # 入场价格
        self.myexitprice = 0.0  # 离场价格
        self.buyorderthisbar = 0  # 该周期是否有交易 0没有,1有
        self.bar_executed = 0  # 记录当前交易的bar序列
        self.turtleunits = 0  # 加仓次数
        self.numlosst = 0  # 统计连续亏损次数
        self.ppunit = 1  # 交易手数比率
        self.positionflag = 0  # 仓位状态 0表示没有仓位，1表示持有多头， -1表示持有空头
        self.radd = 0  # 盈利加仓价格
        self.sexit = 0  # 亏损退出价格
        self.sig_ref1 = 0  # 记录上一次入场信号 1多头,-1空头,0无
        self.sig_long = 0  # 多头条件
        self.sig_short = 0  # 空头条件
        self.sig_longa1 = 0  # 多头加仓条件
        self.sig_shorta1 = 0  # 空头条件
        self.sig_longx1 = 0  # 多头离场条件
        self.sig_shortx1 = 0  # 空头离场条件
        self.mbstop = 0  # 是否触发回撤止损
        self.pl_sum = 0  # 累计连续亏损百分比

        # 建立对于DataFeed的Open/Close价格的引用参数
        self.dtopen = self.datas[0].open
        self.dtclose = self.datas[0].close
        self.dthigh = self.datas[0].high
        self.dtlow = self.datas[0].low
        self.jOpen = self.dtopen  # 开仓条件
        self.jOpen = self.jOpen if abs(self.dtopen[0] - self.jOpen[0]) <= self.p.OCJK else self.dtopen

        # 跟踪挂单
        self.myorder = None

    def start(self):
        """在回测开始之前调用,对应第0根bar"""
        # 回测开始之前的有关处理逻辑可以写在这里
        # 默认调用空的 start() 函数，用于启动回测
        self.myorder = None  # 哨兵避免挂单操作

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        t = 'notify_trade:'
        t += ',盈亏, {:.2f},comm {:.2f}, NET {:.2f}'.format(
            trade.pnl,  # 盈亏
            (trade.pnl - trade.pnlcomm),  # 手续费
            trade.pnlcomm)  # 盈亏含手续费
        t += ',回撤:{:.2f}'.format(self.stats.drawdown.drawdown[0])
        # t += ',收益率:{:.3f}'.format(self.stats.timereturn.line[0])
        t += ',开仓比:{:.0f}%'.format(self.mposkk)

        self.log(t)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # broker 提交/接受了，买/卖订单则什么都不做
            # self.log('order.OrdTypes:{:},size:{:}'.format(order.OrdTypes[order.ordtype], order.size))
            return
        t = 'notify_order:'
        # 检查一个订单是否完成
        # 注意: 当资金不足时，broker会拒绝订单
        if order.status in [order.Completed]:
            if order.isbuy():
                t += ',已买入'
            elif order.issell():
                t += ',已卖出'
            # 记录当前交易数量
            t += (',成交:{:d},持仓:{:d},Price:{:.2f},Cost:{:.2f},Comm:{:.2f}'.format(
                order.executed.size,  # 成交量 开仓数量
                self.position.size,  # 持仓
                order.executed.price,  # 成交价
                order.executed.value,  # 占成交额 用保证金
                order.executed.comm))  # 佣金 手续费
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order.isbuy():
                t += ',买入单'
            elif order.issell():
                t += ',卖出单'
            t += ',订单取消/保证金不足/拒绝'
            t += ',持仓:{:d}'.format(self.position.size)
            t += ',Price:{:.2f}'.format(self.dtclose[0])

        t += ',可用资金:{:.2f}'.format(self.broker.getcash())
        t += ',持仓市值:{:.2f}'.format(self.broker.getvalue(datas=[self.data]))
        t += ',总资产:{:.2f}'.format(self.broker.getvalue())
        t += ',开仓比:{:.0f}%'.format(self.mposkk)

        self.log(t)
        if not order.alive():
            self.myorder = None  # 表示没有订单待处理

    def pos_cash(self, size=None, price=None):
        """开仓金额"""
        poscash = 0.0  # 开仓金额
        price = price if price else self.dtclose[0]

        if self.p.use_target == UseTarget.USE_TARGET_SIZE:  # 按成交量下单
            poscash = abs(size) * bt.Order.comminfo.get_margin(price) * 1.1
        elif self.p.use_target == UseTarget.USE_TARGET_VALUE:  # 按目标金额开仓
            poscash = abs(size)
        elif self.p.use_target == UseTarget.USE_TARGET_PERCENT:  # 百分比开仓
            percent = abs(size / 100)
            poscash = percent * self.broker.getcash()  # 可用资金百分比交易
            # poscash = percent * self.broker.getvalue()  # 帐户总资金百分比交易
            # value1 = self.broker.getvalue(datas=[self.data])  # 占用资金

        return poscash

    def order_target(self, size=None):
        """订单开仓头寸管理"""
        size = size if size else self.mposkk
        dt = self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)

        # if isinstance(data, str):
        #     data = self.getdatabyname(self.data)
        # elif data is None:
        #     data = self.databyname(self.data)
        # print('%04d - %s - Order Target Size: %02d' % (len(self), dt.isoformat(), size))

        poskkcash = 0.0  # 开仓金额
        posmincash = 0.0  # 最小开仓金额
        posmaxcash = 0.0  # 最大开仓金额
        comminfo = self.broker.getcommissioninfo(self.data)
        margin = comminfo.get_margin(self.dtclose[0]) * 1.01  # 最低开仓保证金
        margin_cash = self.broker.getvalue(datas=[self.data])  # 持仓头寸占用资金
        # margin = bt.Order.comminfo.get_margin(self.dtclose[0])  # 最低开仓保证金
        get_cash = abs(self.broker.getcash())  # 可用资金
        sign = np.sign(self.mposkk)  # 取正负符号
        # 按成交量下单
        if self.p.use_target == UseTarget.USE_TARGET_SIZE:
            # self.mposkk = (abs(self.mposkk) + self.mpposmin)
            if size > 0:
                size = (abs(self.position.size) + self.mpposmin)
            elif size < 0:
                size = -(abs(self.position.size) + self.mpposmin)
            poskkcash = margin * abs(size)  # 开仓金额
            posmincash = min(margin * abs(self.mpposmin), get_cash)  # 最小开仓金额
            posmaxcash = min(margin * abs(self.mpposmax), get_cash)  # 最大开仓金额
            # 限定使用资金的范围
            poskkcash = (posmincash * sign if (abs(poskkcash) <= posmincash) else
                         (max(posmincash, posmaxcash) * sign if (abs(poskkcash) > max(posmincash, posmaxcash)) else poskkcash))
            target = int(round(poskkcash // margin))

            self.myorder = self.order_target_size(target=target)
            self.mposkk = size

        else:
            posmincash = min(margin * 1.1, get_cash)  # 最小开仓金额 最低一手交易金额
            posmaxcash = get_cash  # 最大开仓金额 可用资金

            # 按目标金额下单
            if self.p.use_target == UseTarget.USE_TARGET_VALUE:
                poskkcash = self.mposkk  # 开仓金额
                # 限定使用资金的范围
                poskkcash = (posmincash * sign if (abs(poskkcash) <= posmincash) else
                             (max(posmincash, posmaxcash) * sign if (abs(poskkcash) > max(posmincash, posmaxcash)) else poskkcash))
                self.myorder = self.order_target_value(target=poskkcash)
                self.mposkk = poskkcash

            # 按目标百分比下单
            elif self.p.use_target == UseTarget.USE_TARGET_PERCENT:
                # self.mposkk = abs(self.mposkk * (1 + self.mpposmin / 100))
                # self.mposkk += self.mpposmin * self.mpposad
                # self.mposkk += self.mposkk * self.mpposad
                percent = (margin_cash / get_cash)  # 持仓头寸占用总资金比率
                percent = percent if percent else (size / 100)  # 首次开仓使用size%参数
                if size > 0:
                    percent = (abs(percent) * (1 + self.mpposad))
                elif size < 0:
                    percent = -(abs(percent) * (1 + self.mpposad))

                poskkcash = percent * get_cash  # 可用资金百分比交易
                # poskkcash = percent * self.broker.getvalue()  # 帐户总资金百分比交易

                # 限定使用资金的范围
                poskkcash = sign * (  # sign 为开仓方向
                    get_cash if (posmincash > get_cash)  # 最小开仓金额>可用金额时,使用可用金额
                    else (  # 最小开仓金额<可用金额时
                        posmincash if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,使用最小开仓金额
                        else (posmaxcash if (abs(poskkcash) > posmaxcash)  # 开仓金额>最大开仓金额时,使用最大开仓金额
                              else poskkcash)))

                percent = sign * ((abs(poskkcash) + margin_cash) / self.broker.getvalue())  # 计算占用账户总资金的百分比
                # percent = sign * (abs(poskkcash) / get_cash)  # 计算占可用资金百分比 self.myorder = self.order_target_percent(target=percent)
                self.myorder = self.order_target_percent(target=percent)
                # self.mposkk = percent * 100

        return self.myorder

    def next(self):
        # 记录收盘价
        # self.log('Close, %.2f' % self.dtclose[0])
        self.buyorderthisbar = 0  # 标记该周期的交易状态

        # 如果有订单正在挂起，不操作
        if self.myorder:
            return
        # 多头入场条件
        self.sig_long = (
                not self.position  # 空仓时
                and self.dtclose[0] > self.dtopen[0])
        # 空头入场条件
        self.sig_short = (
                not self.position  # 空仓时
                and self.dtclose[0] < self.dtopen[0])
        # 多头加仓条件
        self.sig_longa1 = (self.positionflag == 1) and (self.dthigh[0] > self.dtlow[0]) and (
                self.dtclose[0] >= self.radd) and (self.buyorderthisbar == 0)
        # 空头加仓条件
        self.sig_shorta1 = (self.positionflag == -1 and self.dthigh[0] > self.dtlow[0] and (
                self.dtclose[0] <= self.radd) and self.buyorderthisbar == 0)
        # 多头离场条件 添加OPEN价离场条件
        self.sig_longx1 = (self.positionflag == 1) and self.dthigh[0] > self.dtlow[0] and (
                self.dtclose[0] <= self.sexit or self.dtopen[0] <= self.sexit)
        # 空头离场条件 添加OPEN价离场条件
        self.sig_shortx1 = ((self.positionflag == -1) and self.dthigh[0] > self.dtlow[0] and (
                self.dtclose[0] >= self.sexit or self.dtopen[0] >= self.sexit))

        # t = 'next:'
        t_enter = t_add = t_exit = 'next:'
        assets = self.broker.getvalue()

        # t += ',持仓:{:d}'.format(self.position.size)
        # 如果没有持仓且可用资产>0 时则准备入场
        if not self.position and self.position.size == 0 and (assets > 0):

            if self.sig_long or self.sig_short:
                self.myentryprice = self.dtclose[0]  # 入场价格
                self.myentryprice_begin = self.myentryprice  # 开始入场价格
                self.turtleunits = 1  # 加仓次数
                self.buyorderthisbar = 1  # 标记该周期的交易状态
                self.bar_executed = len(self)  # 记录当前交易的bar序列

            if self.sig_long:  # 买入
                t_enter += ',买入'
                self.sig_ref1 = self.positionflag = 1  # 记录开仓信号
                # self.myorder = self.order_target_percent(target=abs(self.mposkk / 100))  # 百分比开仓
                self.mposkk = abs(self.mposkk + 0.0001)

                self.radd = self.myentryprice * (1 + self.mpr)
                self.sexit = self.myentryprice / (1 + self.mps)

            elif self.sig_short:  # 卖出
                t_enter += ',卖出'
                self.sig_ref1 = self.positionflag = -1  # 记录开仓信号
                # self.myorder = self.order_target_percent(target=-abs(self.mposkk / 100))  # 百分比开仓
                self.mposkk = -abs(self.mposkk * 1 + 0.0001)

                # self.radd = self.myentryprice * (1 - self.mpr)
                # self.sexit = self.myentryprice * (1 + self.mps)
                self.radd = self.myentryprice / (1 + self.mpr)
                self.sexit = self.myentryprice * (1 + self.mps)

            # 入场开仓
            if self.sig_long or self.sig_short:
                self.myorder = self.order_target(self.mposkk)
                if self.myorder and hasattr(self.myorder, 'size'):
                    t_enter += ',开仓中:{:d}'.format(self.myorder.size)
                else:
                    t_enter += ',开仓中'
                t_enter += ',持仓:{:}'.format(self.position.size)
            if self.buyorderthisbar == 1:
                t_enter += ',price:{:.2f}'.format(self.dtclose[0])
                t_enter += ',总资产:{:.2f}'.format(assets)
                # self.log(t_enter)
        # 有持仓时
        else:
            # 盈利加仓
            if self.sig_longa1 or self.sig_shorta1:
                self.myentryprice = self.dtclose[0]  # 入场价格
                self.turtleunits += 1  # 加仓次数加1
                self.buyorderthisbar = 1  # 标记该周期的交易状态
                self.bar_executed = len(self)  # 记录当前交易的bar序列

            # 多头加仓
            if self.sig_longa1:
                t_add += ',买入'
                # self.mposkk = abs(self.mposkk * (1 + self.mpposmin / 100))
                # self.mposkk += self.mpposmin * self.mpposad
                # self.mposkk += self.mposkk * self.mpposad
                # self.mposkk = (abs(self.mposkk) + self.mpposmin)
                self.mposkk = abs(self.mposkk)

                self.radd = self.myentryprice * (1 + self.mpr)
                self.sexit = self.myentryprice / (1 + self.mps)

            # 空头加仓
            if self.sig_shorta1:
                t_add += ',卖出'
                # self.mposkk = -abs(self.mposkk * (1 + self.mpposmin / 100))
                # self.mposkk -= abs(self.mpposmin * self.mpposad)
                # self.mposkk -= abs(self.mposkk * self.mpposad)
                # self.mposkk = -(abs(self.mposkk) + self.mpposmin)
                self.mposkk = -abs(self.mposkk)

                # self.radd = self.myentryprice * (1 - self.mpr)
                # self.sexit = self.myentryprice * (1 + self.mps)
                self.radd = self.myentryprice / (1 + self.mpr)
                self.sexit = self.myentryprice * (1 + self.mps)

            # 加仓日志
            if self.sig_longa1 or self.sig_shorta1:
                self.myorder = self.order_target(self.mposkk)  # 加仓中
                if self.myorder and hasattr(self.myorder, 'size'):
                    t_add += ',加仓中:{:d}'.format(self.myorder.size)
                else:
                    t_add += ',加仓中'
                t_add += ',持仓:{:}'.format(self.position.size)
                t_add += ',price:{:.2f}'.format(self.dtclose[0])
                t_add += ',总资产:{:.2f}'.format(assets)
                # self.log(t_add)

            # 离场 离场价格 SEXIT CLOSE
            if self.sig_longx1 or self.sig_shortx1:
                # 盈利或连续亏损时,减少下次开仓比率
                if self.turtleunits > 1:
                    self.mposkk = (self.mposkk / self.turtleunits)
                elif self.numlosst > 1:
                    self.mposkk = self.mposkk * (1 - self.mpposad)
                self.mposkk = self.mposkk if self.mposkk > self.mpposmin else self.mpposmin
                self.myexitprice = self.dtclose[0]
                self.positionflag = 0  # 清仓后头寸方向为0
                self.turtleunits = 0  # 加仓次数
                self.numlosst += 1  # 统计连续亏损次数
                self.buyorderthisbar = 1  # 标记该周期的交易状态
                self.mbstop = 0

            # 离场平仓
            if self.sig_longx1 or self.sig_shortx1:  # 平仓离场
                # 全部卖出
                self.myorder = self.close()
                t_exit += ',多头' if self.sig_longx1 else ',空头'
                t_exit += ',平仓中:{:}'.format(self.position.size)
                t_exit += ',price:{:.2f}'.format(self.dtclose[0])
                t_exit += ',总资产:{:.2f}'.format(assets)
                # self.log(t_exit)


if __name__ == '__main__':
    runstrat()
