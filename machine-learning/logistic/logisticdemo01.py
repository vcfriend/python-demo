from argparse import Namespace
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# import urllib
args = Namespace(
    seed=1234,
    data_file="titanic.csv",
    train_size=0.75,
    test_size=0.25,
    num_epochs=100,
)
# 设置随机数种子，保证每次数据都相同，便于调试
np.random.seed(args.seed)
# Upload data from GitHub to notebook's local drive
# url = "https://raw.githubusercontent.com/GokuMohandas/practicalAI/master/data/titanic.csv"
# response = urllib.request.urlopen(url)
# html = response.read()
# with open(args.data_file, 'wb') as f:
#     f.write(html)

# 读取数据源 在当前目录下放置titanic.csv，如没有就放开上面注释去下载
df = pd.read_csv(args.data_file, header=0)


# 清理不需要的数据
def preprocess(df):
    # 去掉空数据
    df = df.dropna()
    # 去掉这三类数据
    features_to_drop = ["name", "cabin", "ticket"]
    df = df.drop(features_to_drop, axis=1)
    # 将这三类数据量化
    # 会变为pclass_1	pclass_2	pclass_3	embarked_C	embarked_Q	embarked_S	sex_female	sex_male
    # 是该数据则值为1，不是为0
    categorical_features = ["pclass", "embarked", "sex"]
    df = pd.get_dummies(df, columns=categorical_features)

    return df


# 执行数据处理方法
df = preprocess(df)
# 设置随机生成一定数量的训练数据和测试数据
mask = np.random.rand(len(df)) < args.train_size
train_df = df[mask]
test_df = df[~mask]
# 将survived作为输出结果，区分输入数据和输出数据
X_train = train_df.drop(["survived"], axis=1)
y_train = train_df["survived"]
X_test = test_df.drop(["survived"], axis=1)
y_test = test_df["survived"]
# print(X_train.iloc[0,:])
# print(y_train.iloc[:2])
# 进行数据标准化 此处Y的输出就是0或1，无需标准化
X_scaler = StandardScaler().fit(X_train)
stamdardized_X_train = X_scaler.transform(X_train)
stamdardized_X_test = X_scaler.transform(X_test)
# 使用随机梯度下降算法分类，penalty不使用正则化参数
log_reg = SGDClassifier(loss="log", penalty="none", max_iter=args.num_epochs, random_state=args.seed)
log_reg.fit(X=stamdardized_X_train, y=y_train)
# 进行概率估计，显示的是实际的概率值
pred_test = log_reg.predict_proba(stamdardized_X_test)
# print(pred_test)
# 实际的预测估计，结果是0或1
pred_train = log_reg.predict(stamdardized_X_train)
print(pred_train)
pred_test = log_reg.predict(stamdardized_X_test)
print(pred_test)