# %%
import backtrader as bt
import datetime
from backtrader.dataseries import TimeFrame
import pandas as pd
import math
from multiple_time_class import MultiStrategy

# data=pd.read_csv('1minutes.csv',header=None)
# data[0]=data[0].apply(lambda x:float(x)/1000.0 )
# data_demo= data.tail(60000).to_csv('data_demo.csv',index=False)


cerebro = bt.Cerebro()
data = bt.feeds.GenericCSVData(
    dataname='../../datas/DQC00-1m-2021.txt',
    compression=15,
    timeframe=bt.TimeFrame.Minutes,
    # dtformat=lambda x: datetime.datetime.utcfromtimestamp(float(x)),
    dtformat="%Y%m%d%H%M%S.%f",
    fromdate=datetime.datetime(2021, 3, 1),
    todate=datetime.datetime(2021, 3, 10),
    datetime=1,
    open=2,
    high=3,
    low=4,
    close=5,
    volume=6,
    # openinteres=-1,
)
cerebro.adddata(data, name='hs15m')
cerebro.resampledata(data, name='hs1h', timeframe=bt.TimeFrame.Minutes, compression=60)
cerebro.resampledata(data, name='hs1d', timeframe=bt.TimeFrame.Days)
# cerebro.resampledata(data, name='hs1w', timeframe=bt.TimeFrame.Weeks)
cerebro.addobserver(bt.observers.Trades)
cerebro.addobserver(bt.observers.BuySell)

cerebro.addstrategy(MultiStrategy)

cerebro.broker.setcash(1000000)

cerebro.broker.setcommission(0.002)

cerebro.run()

cerebro.plot(style='bar')
