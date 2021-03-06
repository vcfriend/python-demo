# Code source: Gaël Varoquaux
# Modified for documentation by Jaques Grobler
# License: BSD 3 clause

"""
https://scikit-learn.org/stable/auto_examples/svm/plot_svm_margin.html#sphx-glr-auto-examples-svm-plot-svm-margin-py
下图说明了参数对分隔线的影响。一个大的值基本上告诉我们的模型，我们对数据的分布没有那么多的信心，只会考虑接近分离线的点。CC

较小的值 包括更多/所有观测值，允许使用区域中的所有数据计算边距。C
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from sklearn import svm

# we create 40 separable points
np.random.seed(1)
X = np.r_[np.random.randn(200, 2) - [2, 2], np.random.randn(200, 2) + [2, 2]]
Y = [0] * 200 + [1] * 200

# figure number
fignum = 1

# fit the model
# 参考 https://blog.csdn.net/qq_43043256/article/details/104259061
# for name, penalty in (("unreg", 1), ("reg", 0.05)):
for name, penalty in (("unreg", 1), ):

    clf = svm.SVC(kernel="linear", C=penalty)
    clf.fit(X, Y)

    # get the separating hyperplane #获取分离超平面
    w = clf.coef_[0]  # 获取w

    # 根据超平面 yy= -w0/w1*x1-b1/w1
    a = -w[0] / w[1]  #斜率
    xx = np.linspace(-5, 5)  #公式中的x1
    # 我们得到截距b1和w1后，就可以求出所需要的公式
    # clf.intercept_[0]  #用来获得截距b1(这里共有两个值，分别为到x和到y的)
    yy = a * xx - (clf.intercept_[0]) / w[1]  #超平面


    # plot the parallels to the separating hyperplane that pass through the
    # support vectors (margin away from hyperplane in direction
    # perpendicular to hyperplane). This is sqrt(1+a^2) away vertically in
    # 2-d.
    # 绘制通过的分离超平面的平行线
    # 支持向量(从超平面方向上的边距)
    # 垂直于超平面)。竖直方向上是sqrt(1+a^2)
    # 对于线性回归和逻辑回归，其目标函数为：
    # g(x) = w1x1 + w2x2 + w3x3 + w4x4 + w0
    # coef_和intercept_都是模型参数，即为w
    # coef_为w1到w4
    # intercept_为w0
    # 如果有激活函数sigmoid，增加非线性变化  则为分类  即逻辑回归
    # 如果没有激活函数，则为回归
    # 对于这样的线性函数，都会有coef_和intercept_函数
    margin = 1 / np.sqrt(np.sum(clf.coef_ ** 2))
    yy_down = yy - np.sqrt(1 + a ** 2) * margin  #下边界
    yy_up = yy + np.sqrt(1 + a ** 2) * margin  #上边界

    # plot the line, the points, and the nearest vectors to the plane
    # 绘制直线、点和距离平面最近的向量
    plt.figure(fignum, figsize=(4, 3))
    plt.clf()
    plt.plot(xx, yy, "k-")
    plt.plot(xx, yy_down, "k--")
    plt.plot(xx, yy_up, "k--")

    plt.scatter(
        clf.support_vectors_[:, 0],  #分类0的支持向量
        clf.support_vectors_[:, 1],  #分类1的支持向量
        s=80,
        facecolors="none",
        zorder=10,
        edgecolors="k",
        cmap=cm.get_cmap("RdBu"),
    )
    plt.scatter(
        X[:, 0], X[:, 1], c=Y, zorder=10, cmap=cm.get_cmap("RdBu"), edgecolors="k"
    )

    plt.axis("tight")
    x_min = -4.8
    x_max = 4.2
    y_min = -6
    y_max = 6

    YY, XX = np.meshgrid(yy, xx)
    xy = np.vstack([XX.ravel(), YY.ravel()]).T
    Z = clf.decision_function(xy).reshape(XX.shape)

    # Put the result into a contour plot #将结果放入等高线图
    plt.contourf(XX, YY, Z, cmap=cm.get_cmap("RdBu"), alpha=0.5, linestyles=["-"])

    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    plt.xticks(())
    plt.yticks(())
    fignum = fignum + 1

plt.show()