# %%

# coding=utf8

import pandas as pd
import numpy as np
from sklearn.svm import SVR
import matplotlib.pyplot as plt

plt.style.use(plt.style.available[0])

# %%

# 加载数据
df = pd.read_csv('data/DQC00-1d.txt',
                 sep=',',
                 nrows=5000,
                 index_col=['datetime'],  # 设置行索引
                 parse_dates=['datetime'],  # 解析时间 20100104130500.0
                 date_parser=lambda x: pd.to_datetime(x, format='%Y%m%d%H%M%S.%f'),  # 时间解析的格式，进行毫秒级数据解析
                 usecols=['datetime', 'open', 'high', 'low', 'close', 'volume'],  # 设置需要用到的列
                 encoding='utf-8',
                 float_precision='round_trip',  # 所有数据会当做string读取, 使用时再进行相应的转换为float
                 )
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
# 设定numpy显示浮点数精度的小数位数,不使用科学记数法
np.set_printoptions(precision=2, suppress=True)

# %%

print(df.dtypes)
df.head()

# %%


# %%

# 2.1 缺失值处理

# 检查数据中是否有缺失值，以下两种方式均可
# Flase:对应特征的特征值中无缺失值
# True：有缺失值
print(df.isnull().any())
print(np.isnan(df).any())
# 返回每一列缺失值统计个数
print(df.isnull().sum())

# %%

# 缺失值处理，以下两种方式均可
# 删除包含缺失值的行
df.dropna(inplace=True)
# 缺失值填充
# df.fillna('100')

# 返回每一列缺失值统计个数
df.isnull().sum()

# %%

print(df[:3])
# 2.2 确定特征值 目标值
# 特征值取开盘价和收盘价的差值
X = (df[['open', 'high', 'low']]).values
print(type(X), X.shape, X.ndim)

print(X[:3, ])

# %%

# 目标值取开盘价和收盘价的差值
# y = df.iloc[:, -2:-1].values.ravel()
Y = (df['close']).values
print(Y.shape)
print(Y.ndim)
print(Y[:3])

# %%

# 将数据划分为训练集和验证集
from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(X, Y.reshape(-1, 1),
                                                    random_state=None,
                                                    test_size=0.50,  # 测试集50%样本数量
                                                    shuffle=True,  # default=True 切分前是否对数据进行打乱。
                                                    )

# %%

print(x_train.shape, y_train.shape, y_train.ndim)
print(x_test.shape, y_test.shape, y_test.ndim)
np.hstack((x_test, y_test))[:3]

# %%

## 混淆测试集目标类别的 指定概率50%的错误
err = x_train
for i in range(int(len(err) * 0.0)):
    index = int(np.random.randint(len(err)))
    # index2 = int(np.random.randint(len(err)))
    # err[index,0], err[index,3] = err[index,3], err[index,0]
    err[index] = 0

# %%


# %%

# 3. 特征工程（标准化）
from sklearn.preprocessing import StandardScaler

standardScaler = StandardScaler()

x_train_stand = standardScaler.fit_transform(x_train)
x_test_stand = standardScaler.transform(x_test)

y_train_stand = standardScaler.fit_transform(y_train)
y_test_stand = standardScaler.transform(y_test)

# %%

print(x_train.shape)
print(x_train.ndim)
print(y_train.shape)
print(y_train.ndim)
print(x_train[:10])
print(x_train[:10, 0])

# %%

# 画图观察
# fig, ax = plt.subplots()
# ax.scatter(y_test_stand, x_test_stand)
# ax.plot([y_test_stand.min(), y_test_stand.max()], [y_test_stand.min(), y_test_stand.max()], 'k--', lw=2)
# ax.set_xlabel('Measured')
# ax.set_ylabel('Predicted')
# plt.show()

# %%

# 拟合回归模型
svr_rbf = SVR(kernel='rbf', C=1.00, gamma=1, epsilon=0.05)
svr_lin = SVR(kernel='linear', C=1.00, gamma='auto', epsilon=0.1)
svr_poly = SVR(kernel='poly', C=1.00, gamma='auto',
               degree=3,  # 默认=3 多项式核函数的次数(' poly ')。将会被其他内核忽略。
               epsilon=.15,
               coef0=0.1,  # 默认=0.0 核函数中的独立项。它只在' poly '和' sigmoid '中有意义
               )

# %%

x_train.shape, x_test.shape
# np.vstack((x_train,x_test)).shape

# %%

plt.figure(figsize=(9, 4))  # width, height in inches
n_set_plt = plt.scatter(x_train_stand[:, 0], y_train_stand, c='b', s=5, label='training data')
plt.xlabel('o')
plt.ylabel('c')
plt.title('open close Data Set')
plt.legend(loc="upper left")
plt.savefig(r'./file/02_svm_svr_linear_.png', dpi=200)
plt.show()


# %%

def plot_svm_regression(svm_reg, X, y, axes):
    y_pred = svm_reg.predict(X)
    plt.plot(X[:, 0], y_pred, "k-", linewidth=2, label=r"$\hat{y}$")  # 预测的回归线
    plt.plot(X[:, 0], y_pred + svm_reg.epsilon, "k--")  # 回归线向上平移epsilon
    plt.plot(X[:, 0], y_pred - svm_reg.epsilon, "k--")  # 回归线向下平移epsilon
    plt.scatter(X[svm_reg.support_, 0], y[svm_reg.support_], s=10, facecolors='#FFAAAA')
    plt.plot(X[:, 0], y, "b.", markersize=2)
    plt.xlabel(r"$x_1$", fontsize=18)
    plt.legend(loc="upper left", fontsize=18)
    plt.axis(axes)


plt.figure(figsize=(9, 4))
xx = np.vstack((x_train_stand[:, ], x_test_stand[:, ]))
yy = np.vstack((y_train_stand, y_test_stand))
x_min, x_max = xx.min() - 0.5, xx.max() + 0.5
y_min, y_max = yy.min() - 0.5, yy.max() + 0.5

svrs = [svr_rbf, svr_lin, svr_poly]
kernel_label = ["rbf", "linear", "poly"]
for ix, svr in enumerate(svrs):
    fit = svr.fit(x_train_stand, y_train_stand.ravel())
    # 获取预测值
    y_test_pred = fit.predict(x_test_stand)
    # 显示估计器
    print(f'ix=%s, svcs=%s' % (ix, svrs[ix]))
    # 获取这个估计器的参数
    print(f'估计器的参数: %s' % (svr.get_params()))
    # https://blog.csdn.net/gracejpw/article/details/101546293
    # 返回预测的决定系数R^2
    # R^2越接近于1，模型的拟合优度越高。
    print(f'训练集评分: %s ' % (fit.score(x_train_stand, y_train_stand)))
    print(f'测试集评分: %s ' % (svr.score(x_test_stand, y_test_stand)))

    plt.subplot(1, 3, ix + 1)
    plot_svm_regression(fit, xx, yy, [x_min, x_max, y_min, y_max])
    plt.title(r"${}, \epsilon = {}$".format(fit.kernel, fit.epsilon), fontsize=18)
    plt.ylabel(r"$y$", fontsize=18, rotation=0)

plt.savefig(r'./file/02_svm_svr.png', dpi=200)

# %%

svrs = [svr_rbf, svr_lin, svr_poly]

fit = svrs[0]

print('svm:', fit.support_vectors_.shape)
support_vectors_ = standardScaler.inverse_transform(fit.support_vectors_)
epsilon_1 = standardScaler.inverse_transform(np.array([[fit.epsilon], ]))
epsilon_0 = standardScaler.inverse_transform(np.array([[0.00], ]))
print('epsilon:%s = %s' % (fit.epsilon, epsilon_1 - epsilon_0))

y_test_pred = fit.predict(x_test_stand)
y_test_pred_ = standardScaler.inverse_transform(y_test_pred.reshape(-1, 1))
y_test_ = standardScaler.inverse_transform(y_test_stand.reshape(-1, 1))
y_train_ = standardScaler.inverse_transform(y_train_stand.reshape(-1, 1))
print('mean平均值:', np.mean(abs((y_test_ - y_test_pred_))).round(2))
print('std标准差:', np.std(((y_test_ - y_test_pred_))).round(2))
print('var方差:', np.var(((y_test_ - y_test_pred_))).round(2))
print('svm平均间隔', np.mean(abs(support_vectors_ - epsilon_0)).round(2))
print('svm间隔std', np.std((support_vectors_ - epsilon_0)).round(2))

print('#查看切分后的数据与切分前的数据是否一致', (np.hstack(((y_train[fit.support_]), (y_train_[fit.support_]),
                                          (Y[:len(y_train)][fit.support_].reshape(-1, 1)))))[:5])
print('#查看训练集的支持向量', np.hstack((((x_train)[fit.support_]), (support_vectors_)))[:10])

print('查看预测值与目标值的差值', (np.hstack((x_test, (y_test_pred_ - x_test), (y_test_ - x_test), (y_test - y_test_pred_)))[:5]))

interval = abs(support_vectors_ - epsilon_0)
plt.hist(interval, bins=50)
plt.title('svm interval')
plt.show()

# %%


# %%


# %%

# figure number
fignum = 1
plt.figure(fignum, figsize=(4, 3))

# plt.scatter(np.arange(len(y_test_stand)), y_test_stand, s=5, c='blue')
# plt.scatter(y_test_pred, y_test_pred, s=5, c='r')

plt.show()

# %%

fit = svr_rbf
print('support_支持向量的下标', fit.support_.shape)
print('support_vectors_支持向量', fit.support_vectors_.shape)
print('n_support_每个类别的支持向量数量', fit.n_support_)
print('dual_coef_决策函数中支持向量的系数', fit.dual_coef_.shape)
print('intercept_决策函数中的常量', fit.intercept_)

# %%


# %%
