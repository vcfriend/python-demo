"""
==============================================
Regularization path of L1- Logistic Regression
==============================================


Train l1-penalized logistic regression models on a binary classification
problem derived from the Iris dataset.

The models are ordered from strongest regularized to least regularized. The 4
coefficients of the models are collected and plotted as a "regularization
path": on the left-hand side of the figure (strong regularizers), all the
coefficients are exactly 0. When regularization gets progressively looser,
coefficients can get non-zero values one after the other.

Here we choose the liblinear solver because it can efficiently optimize for the
Logistic Regression loss with a non-smooth, sparsity inducing l1 penalty.

Also note that we set a low value for the tolerance to make sure that the model
has converged before collecting the coefficients.

We also use warm_start=True which means that the coefficients of the models are
reused to initialize the next model fit to speed-up the computation of the
full-path.
在二元分类上训练1-惩罚logistic回归模型
问题源自Iris数据集。
模型由强正则化到最小正则化进行排序。4
模型的系数被收集并绘制成“正规化”
路径“:在图的左侧(强正则化器)，所有的
系数是0。当正规化变得越来越松散时，
系数可以一个接一个地得到非零值。
这里我们选择线性求解器，因为它可以有效地优化
Logistic回归损失与非光滑，稀疏诱导l1惩罚。
还要注意，我们设置了一个较低的公差值，以确保模型
在收集系数之前已经收敛。
我们还使用了warm_start=True，这意味着模型的系数是
用于初始化下一个模型，以加快计算
完整路径。
"""

# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
# License: BSD 3 clause

from time import time
import numpy as np
import matplotlib.pyplot as plt

from sklearn import linear_model
from sklearn import datasets
from sklearn.svm import l1_min_c

iris = datasets.load_iris()
X = iris.data
y = iris.target

X = X[y != 2]
y = y[y != 2]

X /= X.max()  # Normalize X to speed-up convergence

# #############################################################################
# Demo path functions

cs = l1_min_c(X, y, loss="log") * np.logspace(0, 7, 16)


print("Computing regularization path ...")
start = time()
clf = linear_model.LogisticRegression(
    penalty="l1",
    solver="liblinear",
    tol=1e-6,
    max_iter=int(1e6),
    warm_start=True,
    intercept_scaling=10000.0,
)
coefs_ = []
for c in cs:
    clf.set_params(C=c)
    clf.fit(X, y)
    coefs_.append(clf.coef_.ravel().copy())
print("This took %0.3fs" % (time() - start))

coefs_ = np.array(coefs_)
plt.plot(np.log10(cs), coefs_, marker="o")
ymin, ymax = plt.ylim()
plt.xlabel("log(C)")
plt.ylabel("Coefficients")
plt.title("Logistic Regression Path")
plt.axis("tight")
plt.show()
