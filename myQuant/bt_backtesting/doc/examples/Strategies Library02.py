from backtesting.test import SMA
import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from backtesting.lib import SignalStrategy, TrailingStrategy

from backtesting.test import EURUSD, SMA

data = EURUSD.iloc[:, :-1].copy()
print(data.info, data.info())

data['X_Open'] = data.Open
# data['X_High'] = data.High
# data['X_Low'] = data.Low
data['X_Close'] = data.Close
data = data.dropna().astype(float)
print(data.info())

import numpy as np

# 设定numpy显示浮点数精度的小数位数,不使用科学记数法
np.set_printoptions(precision=5, suppress=True)


def get_X(data):
    """返回模型设计矩阵 X"""
    X = data.filter(like='X').values
    # print(X.shape, X.ndim)
    return X


def get_y(data):
    """返回因变量 y
    # 收盘价>开盘价 标记类别为1 收盘价<开盘价 标记类别为-1 收盘价=开盘价 标记类别为0
    """
    epsilon = 0.001  # 误差
    y = (data.Close - data.Open) / data.Open
    y[y.between(-epsilon, epsilon)] = 0  # 货币贬值的回报率低于epsilon
    y[y > 0] = 1
    y[y < 0] = -1
    # print(y.shape, y.ndim)
    return y


def get_clean_Xy(df):
    """返回(X, y)已清除的NaN值"""
    X = get_X(df)
    y = get_y(df).values
    isnan = np.isnan(y)
    X = X[~isnan]
    y = y[~isnan]
    # print(X.shape, X.ndim, y.shape, y.ndim)
    return X, y


from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply


def svc(array, n):
    # print(type(array), array.shape, array.ndim)
    df = array.iloc[:n]
    X, y = get_clean_Xy(df)
    # 初始化我们的模型，分类器
    clf = SVC(kernel='linear', C=100, gamma='scale', probability=False)

    clf.fit(X, y)
    sv_ = clf.support_vectors_

    close = array.Close
    sv_c = np.zeros(len(close), dtype=close.dtype)
    for i, v in enumerate(close):
        sv_min = np.min(abs(sv_ - v))
        sv_c[i] = sv_min + v
    print(type(sv_c), sv_c.shape, sv_c.ndim)
    return pd.Series(sv_c)


class MLTrainOnceStrategy(Strategy):
    price_delta = .004  # 0.4%
    d_svc = 100

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)
        self.daily_svc = None
        # self.forecasts = None
        # self.sv_c = None
        # self.sv_ = None
        # self.clf = None

    def init(self):
        # 在init()和next()中，调用超方法来正确初始化父类是很重要的
        super().init()

        # 为了构建每日svc，我们可以使用库中的' resample_apply() ' helper函数
        self.daily_svc = resample_apply(
            'D', svc, data, self.d_svc)

        # self.sv_c = self.I(sv_cc(self.data, sv_), name='sv_c')
        # self.sv_c = self.I(svc, self.data.Close, sv_)
        pass

    def next(self):
        # 跳过训练、样本内数据
        # if len(self.data) < N_TRAIN:
        #     return

        # 如果sma1交叉高于sma2，关闭所有现有的空头交易，并买入该资产
        if crossover(self.data.Close, self.daily_svc):
            self.position.close()
            self.buy()

        # 否则，如果sma1交叉低于sma2，关闭所有现有的多头交易，并出售资产
        elif crossover(self.daily_svc, self.data.Close):
            self.position.close()
            self.sell()


bt = Backtest(data, MLTrainOnceStrategy, commission=.0002, margin=.05)
bt.run()

bt.plot()
