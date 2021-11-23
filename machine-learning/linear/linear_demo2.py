# 使用sklearn进行线性回归计算
import numpy as np
import pandas as pd
from argparse import Namespace

args = Namespace(
    seed=1234,
    data_file='sample_data.csv',
    num_samples=100,
    train_size=0.75,
    test_size=0.25,
    num_epochs=100,
)
# 设置随机数开始的整数值，保证我们的实验数据是一致的
np.random.seed(args.seed)


def generate_data(num_samples):
    X = np.array(range(num_samples))
    random_noise = np.random.uniform(-10, 10, size=num_samples)
    y = 3.65 * X + 10 + random_noise
    return X, y


# 得到我们需要的x，y数据
X, y = generate_data(args.num_samples)
# 将x,y合并，并转置，然后存储为DataFrame，方便后续操作
data = np.vstack([X, y]).T
df = pd.DataFrame(data, columns=['x', 'y'])

# from sklearn.linear_model.stochastic_gradient import SGDRegressor
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# 得到分类后的测试数据和训练数据，
x_train, x_test, y_train, y_test = train_test_split(df['x'].values.reshape(-1, 1)
                                                    , df['y'], test_size=args.test_size, random_state=args.seed)
# StandardScaler用于标准化数据集
# fit方法计算用于以后缩放的mean和std,默认参数情况下，mean是平均数
# std是标准差，就是所有数减去其平均值的平方和，所得结果除以该组数之个数（或个数减一，即变异数），再把所得值开根号，所得之数就是这组数据的标准差
x_scaler = StandardScaler().fit(x_train)
y_scaler = StandardScaler().fit(y_train.values.reshape(-1, 1))

# transform: 执行数据标准化
# 测试数据和预测数据的标准化的方式要和训练数据标准化的方式一样， 必须用同一个scaler来进行transform
# 数据标准化公式，每个数据均是  (x - 平均值)/标准差
standardized_x_train = x_scaler.transform(x_train)
standardized_y_train = y_scaler.transform(y_train.values.reshape(-1, 1)).ravel()
standardized_x_test = x_scaler.transform(x_test)
standardized_y_test = y_scaler.transform(y_test.values.reshape(-1, 1)).ravel()

# loss:要是用的损失函数，默认是squared_loss，方差拟合
# penalty：使用的惩罚
lm = SGDRegressor(loss='squared_error', penalty='none', max_iter=args.num_epochs)
# 使用梯度下降模型
lm.fit(X=standardized_x_train, y=standardized_y_train)
# predict：进行数据预测
# scaler.var_是方差，np.sqrt(y_scaler.var_)就是标准差,y_scaler.scale_也是标准差，是一样的
# 实际输出结果就是 (模拟的输出结果 * 标准差) + 平均数 和标准化过程刚好相反
pred_train = (lm.predict(standardized_x_train) * y_scaler.scale_) + y_scaler.mean_
pred_test = (lm.predict(standardized_x_test) * np.sqrt(y_scaler.var_)) + y_scaler.mean_

# 测试我们自己的数据
X_infer = np.array((0, 1, 2), dtype=np.float32)
standardized_X_infer = x_scaler.transform(X_infer.reshape(-1, 1))
pred_infer = (lm.predict(standardized_X_infer) * np.sqrt(y_scaler.var_)) + y_scaler.mean_
print(pred_infer)

# Unstandardize coefficients 
# lm.coef_是生成函数系数  lm.intercept_是生成函数的截距
# 进行数据标准化之后，都接近于1，此时x,y均缩小了一定倍数，所以此处还原倍数
# 相当于原来是 y = a * x  缩放成了  (y - y_scaler.mean_)/y_scale.scale_ = lm.coef_ * ((x - x_scaler.mean_) / x_scaler.scale_) + lm.intercept_
# y = lm.coef_ * ((x - x_scaler.mean_) / x_scaler.scale_) * y_scale.scale_ + lm.intercept_ * y_scale.scale_ + y_scaler.mean_
# y = lm.coef_ * (y_scaler.scale_/x_scaler.scale_) * (x - x_scaler.mean_) + lm.intercept_ * y_scale.scale_ + y_scaler.mean_
# y = lm.coef_ * (y_scaler.scale_/x_scaler.scale_) * x - lm.coef_ * (y_scaler.scale_/x_scaler.scale_) * x_scaler.mean_ + lm.intercept_ * y_scale.scale_ + y_scaler.mean_
# 所以真实的a和lm.coef_的倍数关系就是 a = lm.coef_ * (y_scaler.scale_/x_scaler.scale_)
# 真是的b和lm.intercept_的关系是 b = lm.coef_ * (y_scaler.scale_/x_scaler.scale_) * x_scaler.mean_ + lm.intercept_ * y_scale.scale_ + y_scaler.mean_
# 也就是 b = a * x_scaler.mean_ + lm.intercept_ * y_scale.scale_ + y_scaler.mean_
coef = lm.coef_ * (y_scaler.scale_ / x_scaler.scale_)
intercept = lm.intercept_ * y_scaler.scale_ + y_scaler.mean_ - np.sum(coef * x_scaler.mean_)
print(coef)  # ~3.65
print(intercept)  # ~10

# 博客链接https://blog.csdn.net/WonderfulMTF/article/details/89113327
