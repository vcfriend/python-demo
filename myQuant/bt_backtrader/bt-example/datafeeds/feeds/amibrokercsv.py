import backtrader as bt

class AmibrokerCSV(bt.feeds.GenericCSVData):

    params = (
		('dtformat', '%Y%m%d'),
		('tmformat', '%H%M%S'),
		('datetime', 0),
		('time', 1),
		('open', 2),
		('high', 3),
		('low', 4),
		('close', 5),
		('volume', -1),
		('openinterest', -1),
	)
