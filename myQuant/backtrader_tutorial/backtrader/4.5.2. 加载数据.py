#%%
import datetime  #
import os.path  # 路径管理
import sys  # 获取当前运行脚本的路径 (in argv[0])
#导入backtrader框架
import backtrader as bt

# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 保存收盘价的引用
        self.dataclose = self.data_close
        print('切片访问前3个值', self.datas[0].array[:10])
        print('close0',self.dataclose[0],'close1',self.dataclose[1])

    def next(self):
        # 记录收盘价
        self.log('Close, %.2f' % self.dataclose[0])
        pass

# 加载本地csv文件数据
def get_csv_GenericCSVData(stock_id="600016.SH", start="20190101", end="20191231"):
    '''
    # 加载本地csv文件数据
    ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount
    600016.SH,20001219,20.0,21.0,18.5,18.56,11.8,6.76,57.29,1563524.56,3058872.084
    '''
    datapath = os.path.join('./fd_data/600016.SH.csv')
    # 日期格式转换
    dt_start = datetime.datetime.strptime(start, "%Y%m%d")
    dt_end = datetime.datetime.strptime(end, "%Y%m%d")
    # 读取文件
    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(2000, 1, 1),
        todate=datetime.datetime(2000, 12, 31),
        nullvalue=0.0,
        dtformat=('%Y%m%d'),
        datetime=1,
        high=3,
        low=4,
        open=2,
        close=5,
        volume=9,
        openinterest=-1
    )
    return data

if __name__ == '__main__':
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()
    # Cerebro引擎在后台创建broker(经纪人)，系统默认资金量为10000
    # 为Cerebro引擎添加策略
    cerebro.addstrategy(TestStrategy)

    # 获取当前运行脚本所在目录
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    # 拼接加载路径
    # datapath = os.path.join('../../datas/orcl-1995-2014.txt')
    datapath = os.path.join('./fd_data/600016.SH.csv')

    # 创建交易数据集
    data = get_csv_GenericCSVData()

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