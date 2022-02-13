# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.5.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# 多个时间框架
# ============
#
# 依赖技术分析的最佳交易策略可能会考虑多个时间范围内的价格行为。本教程将展示如何使用 _backtesting.py_ 来做到这一点，将大部分工作卸载到
# [pandas resampling](http://pandas.pydata.org/pandas-docs/stable/timeseries.html#resampling).
# 假设您已经熟悉
# [basic framework usage](https://kernc.github.io/backtesting.py/doc/examples/Quick Start User Guide.html).
#
# 我们将对此进行测试
# [400%-a-year trading strategy](http://jbmarwood.com/stock-trading-strategy-300/),
# 每天和每周使用
# [relative strength index](https://en.wikipedia.org/wiki/Relative_strength_index)
# (RSI) values and moving averages (MA).
#
# 在实践中，应该使用指标库中的函数，例如
# [TA-Lib](https://github.com/mrjbq7/ta-lib) or
# [Tulipy](https://tulipindicators.org),
# 但在我们中间，让我们介绍一下我们将使用的两个指标。

# +
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


# -

# 策略大致是这样的:
#
# Buy a position when:
# * weekly RSI(30) $\geq$ daily RSI(30) $>$ 70
# * Close $>$ MA(10) $>$ MA(20) $>$ MA(50) $>$ MA(100)
#
# Close the position when:
# * 每日收盘价超过 2%_below_ MA(10)
# * 8% 固定止损被击中
#
# 我们需要在最低时间范围内（即每天）提供柱数据，并将其重新采样到我们的策略所需的任何更高时间范围（即每周）。
# +
from backtesting import Strategy, Backtest
from backtesting.lib import resample_apply


class System(Strategy):
    d_rsi = 30  # Daily RSI lookback periods
    w_rsi = 30  # Weekly
    level = 70

    def init(self):
        # 计算策略要求的移动平均线
        self.ma10 = self.I(SMA, self.data.Close, 10)
        self.ma20 = self.I(SMA, self.data.Close, 20)
        self.ma50 = self.I(SMA, self.data.Close, 50)
        self.ma100 = self.I(SMA, self.data.Close, 100)

        # 计算每日 RSI(30)
        self.daily_rsi = self.I(RSI, self.data.Close, self.d_rsi)

        # 要构建每周 RSI，我们可以使用库中的 `resample_apply()` 辅助函数
        self.weekly_rsi = resample_apply(
            'W-FRI', RSI, self.data.Close, self.w_rsi)

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
        elif price < .98 * self.ma10[-1]:
            self.position.close()


# -

# 让我们看看我们的策略票价如何在九年的谷歌股票数据上重现。

# +
from backtesting.test import GOOG

backtest = Backtest(GOOG, System, commission=.002)
backtest.run()
# -

# 九年的四笔交易零回报？如果我们稍微优化一下参数呢？

# +
# %%time

# backtest.optimize(d_rsi=range(10, 35, 5),
#                   w_rsi=range(10, 35, 5),
#                   level=range(30, 80, 10))
# -

backtest.plot()

# 更好的。虽然该策略的表现不如简单的买入并持有，但它的曝光率（上市时间）显着降低。
#
# 总之，要在多个时间框架上测试策略，您需要传入最低时间框架的 OHLC 数据，然后将其重新采样到更高的时间框架，应用指标，然后重新采样回更低的时间框架，填写 in-之间。
# 这就是函数 [`backtesting.lib.resample_apply()`](https:kernc.github.iobacktesting.pydocbacktestinglib.htmlbacktesting.lib.resample_apply) 为您所做的。

# Learn more by exploring further
# [examples](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#tutorials)
# or find more framework options in the
# [full API reference](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#header-submodules).
