#%%
# coding=utf-8


import os
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import seaborn as sns
import matplotlib.pyplot as plt
sns.set(style='ticks', context='talk')

if int(os.environ.get("MODERN_PANDAS_EPUB", 0)):
    import prep # noqa
#%%
# 这里我们尝试导入最近5年DJI道琼斯工业股指的最近5年数据。

dji = web.DataReader('^DJI', 'stooq') ##默认导入的是最近5年的数据


df = dji
print(df)
#%%
print(type(df))
print(df.dtypes)
# plt.plot(dji)

#%%
pd.set_option('precision', 2)  # 显示小数点后的位数
# 重新采样5日 周期
dji.resample("5d").mean().head()
#%%
df.resample("W").mean().head()

#%%
df.Close.plot(label='Raw')
df.Close.rolling(28).mean().plot(label='28D MA')
df.Close.expanding().mean().plot(label='Expanding Average')
df.Close.ewm(alpha=0.03).mean().plot(label='EWMA($\\alpha=.03$)')

plt.legend(bbox_to_anchor=(.5, .5))
plt.tight_layout()
plt.ylabel("Close ($)")
sns.despine()
#%%
