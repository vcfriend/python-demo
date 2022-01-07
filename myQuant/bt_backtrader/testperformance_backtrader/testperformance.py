import time, datetime
import backtrader as bt
import os.path  # 管理路径
import sys  # 发现脚本名字
import glob

# 基本上相当于5000只股票，6年的日线数据。双均线策略
STOCKS = 5  # 5000只股票
CANDLES = 1500  # 每只股票1500根k线


# 创建策略类
class SmaCross(bt.Strategy):
    # 定义参数
    params = dict(
        fast_period=5,  # 快速移动平均期数
        slow_period=10, )  # 慢速移动平均期数

    def __init__(self):
        self.i = 0
        self.dtinit = datetime.datetime.now()
        print('Strat Init Time:             {}'.format(self.dtinit))
        loaddata = (self.dtinit - self.env.dtcerebro).total_seconds()
        print('Time Loading Data Feeds:     {:.2f}'.format(loaddata))

        print('Number of data feeds:        {}'.format(len(self.datas)))

        # 股票stock的快速移动平均线指标
        fastMA = {stock: bt.ind.MovingAverageSimple(stock, period=self.params.fast_period) for stock in self.datas}

        # 股票stock的慢速移动平均线指标
        slowMA = {stock: bt.ind.MovingAverageSimple(stock, period=self.params.slow_period) for stock in self.datas}

        # 股票stock的移动均线交叉信号指标
        self.crossover = {stock: bt.ind.CrossOver(fastMA[stock], slowMA[stock]) for stock in self.datas}

        self.orderlist = []  # 以往订单列表

    def start(self):
        self.dtstart = datetime.datetime.now()
        print('Strat Start Time:            {}'.format(self.dtstart))

    def prenext(self):
        if len(self.data0) == 1:  # only 1st time
            self.dtprenext = datetime.datetime.now()
            print('Pre-Next Start Time:         {}'.format(self.dtprenext))
            indcalc = (self.dtprenext - self.dtstart).total_seconds()
            print('Time Calculating Indicators: {:.2f}'.format(indcalc))

    def nextstart(self):
        if len(self.data0) == 1:  # there was no prenext
            self.dtprenext = datetime.datetime.now()
            print('Pre-Next Start Time:         {}'.format(self.dtprenext))
            indcalc = (self.dtprenext - self.dtstart).total_seconds()
            print('Time Calculating Indicators: {:.2f}'.format(indcalc))

        self.dtnextstart = datetime.datetime.now()
        print('Next Start Time:             {}'.format(self.dtnextstart))
        warmup = (self.dtnextstart - self.dtprenext).total_seconds()
        print('Strat warm-up period Time:   {:.2f}'.format(warmup))
        nextstart = (self.dtnextstart - self.env.dtcerebro).total_seconds()
        print('Time to Strat Next Logic:    {:.2f}'.format(nextstart))
        self.next()

    def next(self):  # 每个新bar触发调用一次，相当于其他框架的 on_bar()方法
        self.i += 1
        # print('next',self.i, datetime.datetime.now())
        for o in self.orderlist:
            self.cancel(o)  # 取消以往所有订单
            self.orderlist = []  # 置空

        for stock in self.datas:
            if not self.getposition(stock):  # 还没有仓位，才可以买
                if self.crossover[stock] > 0:  # 金叉           
                    order = self.buy(data=stock, size=100)
                    self.orderlist.append(order)

            # 已有仓位，才可以卖
            elif self.crossover[stock] < 0:  # 死叉          
                order = self.sell(data=stock, size=100)
                self.orderlist.append(order)

    def stop(self):
        dtstop = datetime.datetime.now()
        print('End Time:                    {}'.format(dtstop))
        nexttime = (dtstop - self.dtnextstart).total_seconds()
        print('Time in Strategy Next Logic: {:.2f}'.format(nexttime))
        strattime = (dtstop - self.dtprenext).total_seconds()
        print('Total Time in Strategy:      {:.2f}'.format(strattime))
        totaltime = (dtstop - self.env.dtcerebro).total_seconds()
        print('Total Time:                  {:.2f}'.format(totaltime))
        print('Length of data feeds:        {}'.format(len(self.data)))


##########################
# 主程序开始
#########################
cerebro = bt.Cerebro()  # stdstats=False

datadir = './testdatacsv'  # 数据文件位于本脚本所在目录的data子目录中
datafilelist = glob.glob(os.path.join(datadir, '*'))  # 数据文件路径列表

maxstocknum = 5  # 股票池最大股票数目

# 注意，排序第一个文件必须是指数数据，作为时间基准
datafilelist = datafilelist[0:maxstocknum]  # 截取指定数量的股票池
# print(datafilelist)


# 将目录datadir中的数据文件加载进系统
for fname in datafilelist:
    data = bt.feeds.GenericCSVData(
        dataname=fname,
        timeframe=bt.TimeFrame.Minutes,

    )

    cerebro.adddata(data)

cerebro.addstrategy(SmaCross)
startcash = 10000000
cerebro.broker.setcash(startcash)

cerebro.dtcerebro = dt0 = datetime.datetime.now()
print('Cerebro Start Time:          {}'.format(dt0))
results = cerebro.run()

# print ('run finish', time.strftime('%H:%M:%S',time.localtime(time.time())))

print('最终市值: %.2f' % cerebro.broker.getvalue())
