from __future__ import (absolute_import, division, print_function,
						unicode_literals)

import argparse

import backtrader as bt

class DataStrategy(bt.Strategy):
	params = (
		('dtfmt', '%Y-%m-%dT%H:%M:%S.%f'),
	)
	def __init__(self):
		pass

	def prenext(self):
		print('** prenext')
# 		self.next()

	def nextstart(self):
		print('-- nextstart called with len {}'.format(len(self)))
		print('Data0, {}'.format(self.data.datetime.datetime(0).strftime(self.p.dtfmt)))
		print('Data1, {}'.format(self.data1.datetime.datetime(0).strftime(self.p.dtfmt)))

	def next(self):
		print('Strategy: Bar({})'.format(len(self)))

		txt = list()
		txt.append('Data0')
		txt.append('%04d' % len(self.data0))
		txt.append('{:f}'.format(self.data.datetime[0]))
		txt.append('%s' % self.data.datetime.datetime(0).strftime(self.p.dtfmt))
		# txt.append('{:f}'.format(self.data.open[0]))
		# txt.append('{:f}'.format(self.data.high[0]))
		# txt.append('{:f}'.format(self.data.low[0]))
		txt.append('{:f}'.format(self.data.close[0]))
		# txt.append('{:6d}'.format(int(self.data.volume[0])))
		# txt.append('{:d}'.format(int(self.data.openinterest[0])))
		# txt.append('{:f}'.format(self.sma_small[0]))
		print(', '.join(txt))

		if len(self.datas) > 1 and len(self.data1):
			txt = list()
			txt.append('Data1')
			txt.append('%04d' % len(self.data1))
			txt.append('{:f}'.format(self.data1.datetime[0]))
			txt.append('%s' % self.data1.datetime.datetime(0).strftime(self.p.dtfmt))
			# txt.append('{}'.format(self.data1.open[0]))
			# txt.append('{}'.format(self.data1.high[0]))
			# txt.append('{}'.format(self.data1.low[0]))
			txt.append('{}'.format(self.data1.close[0]))
			# txt.append('{}'.format(self.data1.volume[0]))
			# txt.append('{}'.format(self.data1.openinterest[0]))
			# txt.append('{}'.format(float('NaN')))
			print(', '.join(txt))

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

	cerebro.adddata(data)

	# Resample the data
	if args.noresample:
		datapath = '../datas/2006-week-001.txt'
		data2 = bt.feeds.BacktraderCSVData(
			dataname=datapath)
		cerebro.adddata(data2)
	else:
		# New resampler
		cerebro.resampledata(
			data,
			timeframe=bt.TimeFrame.Weeks,
			compression=1)

	# Run over everything
	cerebro.run()

	# Plot the result
#	cerebro.plot(style='bar')


def parse_args():
	parser = argparse.ArgumentParser(
		description='Lifecycle')

	parser.add_argument('--noresample', action='store_true',
						help='Do not resample, rather load larger timeframe')

	return parser.parse_args()


if __name__ == '__main__':
	runstrat()