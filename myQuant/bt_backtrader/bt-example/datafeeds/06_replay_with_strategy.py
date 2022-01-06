from __future__ import (absolute_import, division, print_function,
						unicode_literals)

import argparse

import backtrader as bt

class DataStrategy(bt.Strategy):
	params = (
		('dtfmt', '%Y-%m-%dT%H:%M:%S.%f'),
		('period', 10),
	)
	def __init__(self):
#		pass
#		self.sma = bt.indicators.SMA(self.data, period=self.p.period)
		self.last_bar = len(self)

	def start(self):
		self.counter = 0

#	def prenext(self):
#		self.counter += 1
#		print('prenext len({}) - counter({})'.format(len(self), self.counter))

	def next(self):
		self.counter += 1
		print('--next len({}) - counter({})'.format(len(self), self.counter))
		print('last bar {}'.format(self.last_bar))
		self.log('Open: {:.2f} High: {:.2f} Low: {:.2f} Close: {:.2f}'.format(self.data.open[0], self.data.high[0], self.data.low[0], self.data.close[0]))
		print('last bar of large TF')
		self.log('Open: {:.2f} High: {:.2f} Low: {:.2f} Close: {:.2f}'.format(self.data.open[-1], self.data.high[-1], self.data.low[-1], self.data.close[-1]))
		bar = len(self)

		if not self.position and bar > self.last_bar:
			pass

		self.last_bar = bar

	def log(self, txt, dt=None):
		''' Logging function for this strategy'''
		dt = dt or self.datas[0].datetime.datetime(0)
		print('%s:: %s' % (dt.isoformat(), txt))

def runstrat():
	args = parse_args()

	# Create a cerebro entity
	cerebro = bt.Cerebro(stdstats=False)

	# Add a strategy
	cerebro.addstrategy(DataStrategy)

	# Load the Data
	datapath = '../datas/2006-day-001.txt'
	data = bt.feeds.BacktraderCSVData(
		dataname=datapath)


	# Add original data - smaller timeframe
	cerebro.replaydata(
			data,
			timeframe=bt.TimeFrame.Weeks,
			compression=1)

	# Run over everything
	cerebro.run()

	# Plot the result
#	cerebro.plot(style='bar')


def parse_args():
	parser = argparse.ArgumentParser(
		description='Replay')

	return parser.parse_args()


if __name__ == '__main__':
	runstrat()