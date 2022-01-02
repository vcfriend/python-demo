import tushare as ts
import pandas as pd
import numpy as np
import backtrader as bt
import datetime as dt
from SimpleStrategy import *

# TOKEN = 'cd9e075edc5e5106a21a9c38b42a4e92744e08e91405c977e52e69ff'
TOKEN = '76d0121aa860eb7945280ee984bdf91caa7293a58d90ce737c3c4e4a'
pro = ts.pro_api(token=TOKEN)

data = {
    'code':['600819.SH','000612.SZ','000998.SZ','002009.SZ','300159.SZ',
    '300048.SZ','600150.SH','002041.SZ','601669.SH','002368.SZ'],
    'name':['耀皮玻璃','焦作万方','隆平高科','天奇股份','新研股份','合康新能','中国船舶','登海种业','中国电建','太极股份']
}

frame = pd.DataFrame(data)[:2]  #测试前几个合约
stock = frame['code']
print(stock)


def fetch_daily_data(stock, start, end):
    data = pro.daily(ts_code=stock, start_date=start, end_date=end)
    data['trade_date'] = pd.to_datetime(data['trade_date'])
    data = data.sort_values(by='trade_date')
    data.index = data['trade_date']
    # data.index = pd.to_datetime(data['trade_date'])
    data = data[
        ['ts_code', 'open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']]
    return data


for i in range(len(stock)):
    data = fetch_daily_data(stock.iloc[i], '20210101', '20210813')  # 字段分别为股票代码、开始日期、结束日期
    data.to_csv(r'..\..\datas\\' + stock.iloc[i] + '.csv')

cerebro = bt.Cerebro()
for i in range(len(stock)):  # 循环获取10支股票历史数据
    data = bt.feeds.GenericCSVData(
        dataname=r'..\..\datas\\' + stock.iloc[i] + '.csv',
        fromdate=dt.datetime(2020, 8, 13),
        todate=dt.datetime(2021, 8, 13),
        dtformat='%Y-%m-%d',
        datetime=0,  # 定义trade_date在第0列
        open=2,
        high=3,
        low=4,
        close=5,
        volume=9,
        nullvalue=0.0,  # 设置空值
    )
    cerebro.adddata(data)
# 回测设置
startcash = 100000.0
cerebro.broker.setcash(startcash)
# 设置佣金为万分之二
cerebro.broker.setcommission(commission=0.0002)
# 添加策略
cerebro.addstrategy(SimpleStrategy, printlog=True)
cerebro.run()
# 获取回测结束后的总资金
portvalue = cerebro.broker.getvalue()
pnl = portvalue - startcash
# 打印结果
print(f'总资金: {round(portvalue, 2)}')
print(f'净收益: {round(pnl, 2)}')
# 绘图，暂时先不测试了
cerebro.plot()
