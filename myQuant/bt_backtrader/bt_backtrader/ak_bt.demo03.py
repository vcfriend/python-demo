import akshare
from datetime import datetime
import backtrader as bt


# 使用 akshare 从网络加载数据源
def get_akshare_online_daily_data(
        code: str = "000001",
        date_start: str = "20190101",
        date_end: str = "20191231",
        format="%Y%m%d", ):
    """利用 AKShare 获取股票的后复权数据，这里只获取前 6 列
    """
    try:
        # 利用 AKShare 获取股票的后复权数据，这里只获取前 6 列
        df = akshare.stock_zh_a_hist(symbol=code, start_date=date_start, end_date=date_end, adjust="hfq").iloc[:, :6]
        # 处理字段命名，以符合 Backtrader 的要求
        df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', ]
        # 列名修改成指定的
        # df.rename(columns={"vol": "volume"}, inplace=True)

        # print(df.shape[0])
        # print(df.info())
        # print(df.head())
        # 使用pandas数据源创建交易数据集
        data = bt.feeds.PandasData(dataname=df)

        return data
    except Exception as err:
        print("下载{0}完毕失败！")
        print("失败原因 = " + str(err))


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 保存收盘价的引用
        self.dataclose = self.data0_close
        print('切片访问close前10个值', self.data0_close.array[:10])
        print('切片访问close后3个值', self.data0_close.array[-3:])
        print('切片访问close后3个值', self.data0_close.get(ago=-1, size=3))
        print('切片访问open后3个值', self.data0_open.get(ago=-1, size=3))
        print('close0', self.data0_close[0], 'close1', self.data0_close[1], 'close-1', self.data0_close[-1])

        print("---------------")

    def next(self):
        # 记录收盘价
        # self.log('Close, %.2f' % self.dataclose[0])
        print('open:', self.data_open[0],
              'high:', self.data_high[0],
              'low:', self.data_low[0],
              'close:', self.data_close[0],
              )
        pass


if __name__ == '__main__':
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()
    # Cerebro引擎在后台创建broker(经纪人)，系统默认资金量为10000
    # 为Cerebro引擎添加策略
    cerebro.addstrategy(TestStrategy)

    code = "000001"
    date_start = "20190101"
    date_end = "20191231"
    format = "%Y%m%d"

    # 使用 akshare 从网络加载数据源
    data = get_akshare_online_daily_data(code, date_start, date_end, format)

    # 加载交易数据
    cerebro.adddata(data)

    # 设置投资金额100000.0
    cerebro.broker.setcash(100000.0)
    # 引擎运行前打印期出资金
    print('组合期初资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    # 引擎运行后打期末资金
    print('组合期末资金: %.2f' % cerebro.broker.getvalue())

    print('data', data)
    # os.system("pause")
