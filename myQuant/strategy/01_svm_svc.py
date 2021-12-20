# %%

# coding=utf8

import pandas as pd
import numpy as np
from sklearn.svm import SVC
import matplotlib.pyplot as plt

# %%

# 加载数据
df = pd.read_csv('data/DQC00-1d.txt',
                 sep=',',
                 nrows=3000,
                 index_col=['datetime'],  # 设置行索引
                 parse_dates=['datetime'],  # 解析时间 20100104130500.0
                 date_parser=lambda x: pd.to_datetime(x, format='%Y%m%d%H%M%S.%f'),  # 时间解析的格式，进行毫秒级数据解析
                 usecols=['datetime', 'open', 'high', 'low', 'close', 'volume'],  # 设置需要用到的列
                 encoding='utf-8',
                 float_precision='round_trip',  # 所有数据会当做string读取, 使用时再进行相应的转换为float
                 )
# %%

# pd.reset_option('display.float_format')  # 重置
pd.set_option('precision', 2)  # 显示小数点后的位数
pd.set_option('display.max_rows', 300)  # 控制显示的最大行数
pd.set_option('display.min_rows', 20)  # 确定显示的部分有多少行
# pd.set_option('display.float_format',  '{:,.2f}'.format) # 数字格式化显示 用逗号格式化大值数字 设置数字精度
# 指定列名设置计算精确度，未指定的保持原样
df.round({'open': 0, 'high': 0, 'low': 0, 'close': 0})
# 统一保持1位小数
df.round(0)
# 设置np输出精度
np.set_printoptions(precision=2)

# %%

print(df.dtypes)
df.head()
# %%
# 2.1 缺失值处理

# 检查数据中是否有缺失值，以下两种方式均可
# Flase:对应特征的特征值中无缺失值
# True：有缺失值
print(df.isnull().any())
print(np.isnan(df).any())
# 删除包含缺失值的行
df.dropna(inplace=True)
# 返回每一列缺失值统计个数
print(df.isnull().sum())
# %%

# 2.2 确定特征值 目标值
# 特征值取 开 高 低 收 价
X = df.loc[:, ['open', 'high', 'low', 'close']].values
print(X.shape)
print(X.ndim)
print(X[:3, ])

# %%


# 收盘价>开盘价 标记为类别1 收盘价<=开盘价 标记为类别0
df['flag'] = df.apply(lambda x: 0 if (x['open'] > x['close']) else 1, axis=1)

# # 收盘价>开盘价 标记类别为1 收盘价<开盘价 标记类别为-1 收盘价=开盘价 标记类别为0
# epsilon = 0.1  #误差
# df['flag'] = df.apply(
#     lambda x: 0 if (abs(x['close'] - x['open']) <= epsilon)
#     else ( 1 if (x['close'] - x['open'] > epsilon) else -1), axis=1)

print(df.head())

# 目标值取收盘
y = df.loc[:, 'flag'].values
print(y.shape)
print(y.ndim)
print(y[:3])
y1 = y.copy()

# %%

# 将数据划分为训练集和验证集
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)

# %%
## 混淆测试集目标类别的 指定概率50%的错误
err = y_train
for i in range(int(len(err) * 0.8)):
    index = int(np.random.randint(len(err)))
    err[index] = 0 if err[index] == 1 else 1

# %%

print(y_train[:100])
print(y_test[:100])
# %%

print(X_train[:3])
print(X_test[:3])
print(y_train[:3])
print(y_test[:3])

# %%

# 3. 特征工程（标准化）
from sklearn.preprocessing import StandardScaler

standardScaler = StandardScaler()

# 测试集 计算平均值和标准偏差
standardScaler.fit(X_train)
# 缩放测试集
x_train_stand = standardScaler.transform(X_train)
# 重新计算平均值和标准偏差 并缩放测试集
x_test_stand = standardScaler.transform(X_test)

# %%
# 目标类别为0，1 不用标准化
print(y_train[:10])
# %%

# 拟合分类模型
svr_rbf = SVC(kernel='rbf', C=10, gamma=1)
svr_lin = SVC(kernel='linear', C=10, gamma='auto')
svr_poly = SVC(kernel='poly', C=10, gamma='auto', degree=3, coef0=1)

# %%

svcs = [svr_rbf, svr_lin, svr_poly]
kernel_label = ["rbf", "linear", "poly"]
for ix, svc in enumerate(svcs, start=2):  # 从下标0开始，返回svcs中的下标和值
    performance = svc.fit(x_train_stand, y_train.ravel())
    # 获取预测值
    y_test_pred = performance.predict(x_test_stand)
    # 显示估计器
    print(f'ix=%s, svcs=%s' % (ix, svcs[ix]))
    # 获取这个估计器的参数
    print(f'估计器的参数: %s' % (svc.get_params()))
    # https://blog.csdn.net/gracejpw/article/details/101546293
    # 返回预测的决定系数R^2
    # R^2越接近于1，模型的拟合优度越高。
    print(f'训练集评分: %s ' % (performance.score(x_train_stand, y_train)))
    print(f'测试集评分: %s ' % (svc.score(x_test_stand, y_test)))

# %%


# %%
print(x_train_stand.shape)
print(x_test_stand.shape)
print(y_train.shape)
print(y_train.ndim)
print(x_test_stand[:5])
print(y_test_pred[:50])
# %%


# %%
print(y_test.shape)
print(y_test.sum())
print(y_test_pred.sum())
# %%
