import os
import calendar
import datetime
import backtrader as bt

from strategy.teststrategy import TestStrategy

class RollStrategy(bt.Strategy):

	def start(self):
		header = ['Len', 'Name', 'RollName', 'Datetime', 'WeekDay', 'Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest']
		print(', '.join(header))

	def next(self):
		txt = list()
		txt.append('%04d' % len(self.data0))
		txt.append('{}'.format(self.data0._dataname))
		# Internal knowledge ... current expiration in use is in _d
		txt.append('{}'.format(self.data0._d._name))
		txt.append('{}'.format(self.data.datetime.date()))
		txt.append('{}'.format(self.data.datetime.date().strftime('%a')))
		txt.append('{}'.format(self.data.open[0]))
		txt.append('{}'.format(self.data.high[0]))
		txt.append('{}'.format(self.data.low[0]))
		txt.append('{}'.format(self.data.close[0]))
		txt.append('{}'.format(self.data.volume[0]))
		txt.append('{}'.format(self.data.openinterest[0]))
		print(', '.join(txt))

def checkdate(dt, d):
	# check if date is in the week where the 3rd friday of Mar/Jun/Sep/Dec

	# Future expiry codes: MYY
	# M -> H, M, U, Z (Mar, Jun, Sep, Dec)
	# YY -> 19 20 (2019, 2020)
	MONTHS = dict(H=3, M=6, U=9, Z=12)
	M = MONTHS[d._name[-3]]

	centuria, year = divmod(dt.year, 100)
	decade = centuria * 100

	ycode = int(d._name[-2:])
	yy = decade + ycode

	exp_day = 21 - (calendar.weekday(yy, M, 1) + 2) % 7
	exp_dt = datetime.datetime(yy, M, exp_day)

	# get year, week numbers
	exp_year, exp_week, _  = exp_dt.isocalendar()
	dt_year, dt_week, _ = dt.isocalendar()

	print('dt {} vs {} exp_dt'.format(dt, exp_dt))
	print('dt_week {} vs {} exp_week'.format(dt_week, exp_week))

	# can switch if in same week
	return (dt_year, dt_week) == (exp_year, exp_week)

def checkvolume(d0, d1):
	return d0.volume[0] < d1.volume[0]

def runstrat():
	cerebro = bt.Cerebro()

	cerebro.addstrategy(RollStrategy)

	datapath = '../datas'
	fcon = ['S50H19', 'S50M19', 'S50U19', 'S50Z19']

	rollkwargs = {}
# 	rollkwargs['checkdate'] = checkdate
# 	rollkwargs['checkcondition'] = checkvolume

	datas = [bt.feeds.GenericCSVData(dataname=os.path.join(datapath, f"{f}.csv"), name=f, dtformat='%Y-%m-%d', volume=8, openinterest=9) for f in fcon ]

	data_con = bt.feeds.RollOver(*datas, dataname="S50_COI", **rollkwargs)
	cerebro.adddata(data_con)
	# or
#	cerebro.rolloverdata(*datas, name="S50_COI", **rollkwargs)

	cerebro.run(stdstats=False)

	cerebro.plot()

if __name__ == '__main__':
	runstrat()