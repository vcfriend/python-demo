import numpy as np
import pandas as pd
from numpy import dot
from numpy.linalg import inv
from argparse import Namespace
import matplotlib.pyplot as plt

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
df = pd.DataFrame(data, columns=['x1', 'y'])
# 设置x0参数，方便我们后续建模，前文已经解释过了
df['x0'] = 1
# 取出操作过后的x和y矩阵，并且改变y的shape，是为了后续矩阵计算使用
X = df.iloc[:, [2, 0]]
Y = df.iloc[:, 1].values.reshape(args.num_samples, 1)
# 数学计算，最小二乘法得到结果的公式
theta2 = dot(dot(inv(dot(X.T, X)), X.T), Y)
print(theta2)
theta2 = theta2.reshape(1, 2)[0]

theta = np.array([1., 1.]).reshape(2, 1)
alpha = 0.0001
temp = theta
# 初始化x0,x1的参数矩阵
x0 = X.iloc[:, 0].values.reshape(args.num_samples, 1)
x1 = X.iloc[:, 1].values.reshape(args.num_samples, 1)

for i in range(10000):
    # 分别计算两个参数的向量，并且将源数据进行一定程度的变更
    temp[0] = theta[0] - alpha * np.sum((dot(X, theta) - Y) * x0) / args.num_samples
    temp[1] = theta[1] - alpha * np.sum((dot(X, theta) - Y) * x1) / args.num_samples
    # 用新学会的数据替换旧数据
    theta = temp
print(theta.reshape(1, 2))
theta = theta.reshape(1, 2)[0]
newX = np.array(range(100))
newY = theta[1] * newX + theta[0]
newY2 = theta2[1] * newX + theta2[0]
plt.title('Generated data')
plt.scatter(x=df['x1'], y=df['y'])
plt.plot(newX, newY, color="red", linewidth=1, linestyle="-", label="tidu")
plt.plot(newX, newY2, color="yellow", linewidth=1, linestyle="-", label="math2")
plt.legend(loc='lower right')
plt.show()
