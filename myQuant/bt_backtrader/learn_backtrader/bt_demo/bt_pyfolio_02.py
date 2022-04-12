import datetime

import backtrader as bt
import backtrader.analyzers as btanalyzers
import backtrader.feeds as btfeeds
import backtrader.strategies as btstrats

cerebro = bt.Cerebro()

dataname = '../data/2005-2006-day-001.txt'
data = btfeeds.BacktraderCSVData(dataname=dataname)
cerebro.adddata(data)
cerebro.addstrategy(btstrats.SMA_CrossOver)


#……策略和参数
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')
back = cerebro.run()
strat = back[0]
portfolio_stats = strat.analyzers.getbyname('PyFolio')
returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
print(returns)
returns.index = returns.index.tz_convert(None)
import pandas as pd
import quantstats
quantstats.reports.html(returns, output='stats.html', title='BTC Sentiment')

