import backtrader as bt
from .amibrokercsv import AmibrokerCSV

class AmibrokerCSVPE(AmibrokerCSV):
	# Add a 'pe' line to the inherited ones from the base class
	lines = ('pe',)

	# add the parameter to the parameters inherited from the base class
	params = (
		('pe', 6),
	)
