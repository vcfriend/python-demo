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
		pass


	def start(self):
		self.counter = 0

#	def prenext(self):
#		self.counter += 1
#		print('prenext len({}) - counter({})'.format(len(self), self.counter))

	def next(self):
		self.counter += 1
		print('--next len({}) - counter({})'.format(len(self), self.counter))

		# work on last tick of bar
		if not self.position and self.counter == 5:
			self.counter = 0

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