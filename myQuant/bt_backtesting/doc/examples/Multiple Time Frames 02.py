import pandas as pd


def SMA(array, n):
    """Simple moving average"""
    return pd.Series(array).rolling(n).mean()


def RSI(array, n):
    """相对强度指数"""
    # 近似;够好了
    gain = pd.Series(array).diff()
    loss = gain.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    rs = gain.ewm(n).mean() / loss.abs().ewm(n).mean()
    return 100 - 100 / (1 + rs)


from backtesting import Strategy, Backtest
from backtesting.lib import resample_apply
import backtesting.lib as btlib


class System(Strategy):
    d_rsi = 5  # Daily RSI lookback periods
    w_rsi = 5  # Weekly
    level = 70

    def init(self):
        # 让我们将收盘价转换回熊猫系列。
        close = self.data.Close.s
        # 重新采样为每日分辨率。使用最后一个值（即一天结束时的收盘价）聚合组。
        # 注意`label='right'`。如果将其设置为“左”（默认），则该策略将表现出前瞻性偏差。
        close_daily = close.resample('D', label='right').agg('last')
        data_daily = self.data.df.resample('D', label='right').agg(btlib.OHLCV_AGG).dropna()
        # 计算策略要求的移动平均线
        self.ma10 = self.I(SMA, self.data.Close, 10)
        self.ma20 = self.I(SMA, self.data.Close, 20)
        self.ma50 = self.I(SMA, self.data.Close, 50)
        self.ma100 = self.I(SMA, self.data.Close, 100)




        # 计算每日 RSI(30)
        self.daily_rsi = resample_apply('D', RSI, self.data.Close, self.d_rsi)

        # 要构建每周 RSI，我们可以使用库中的 `resample_apply()` 辅助函数
        self.weekly_rsi = resample_apply('W-FRI', RSI, self.data.Close, self.w_rsi)

    def next(self):
        price = self.data.Close[-1]

        # 如果我们还没有持仓，并且满足所有条件，则输入多头。
        if (not self.position and
                self.daily_rsi[-1] > self.level and
                self.weekly_rsi[-1] > self.level and
                self.weekly_rsi[-1] > self.daily_rsi[-1] and
                self.ma100[-1] < self.ma50[-1] < self.ma20[-1] < self.ma10[-1] < price):

            # 下次开盘时以市价买入，但要设置 8% 的固定止损。
            self.buy(sl=.92 * price)

        # 如果价格收盘价低于 10 日均线 2% 或更多，则平仓（如果有）。
        elif price < .98 * self.ma100[-1]:
            self.position.close()


# -

# 让我们看看我们的策略票价如何在九年的谷歌股票数据上重现。

# +
from backtesting.test import EURUSD

EURUSD_D = EURUSD.resample('D', label='right').agg(btlib.OHLCV_AGG).dropna()
backtest = Backtest(EURUSD, System, commission=.002)
backtest.run()

backtest.plot()
