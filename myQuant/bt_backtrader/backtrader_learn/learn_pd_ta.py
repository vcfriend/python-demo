# %%
import pandas_ta as ta
import pandas as pd

# %%
df = pd.read_csv('E:\Quant\Bitcoin autotrade//15min.csv', usecols=range(0, 6), \
                 names=['time', 'open', 'high', 'low', 'close', 'volume', ], header=None)
# df['time'] = pd.to_datetime(df['time'],unit='ms')
# %%
df['ema'] = ta.ema(df['close'])
