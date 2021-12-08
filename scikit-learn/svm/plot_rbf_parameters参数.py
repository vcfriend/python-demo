"""
==================
RBF SVM parameters
==================

这个例子说明了径向基函数(RBF)核SVM的参数“gamma”和“C”的效果。
直观地说，“gamma”参数定义了单个训练示例的影响达到的程度，值低表示“远”，值高表示“近”。参数可以看作是模型选择的样本作为支持向量的影响半径的倒数。
“C”参数在训练示例的正确分类与决策函数的边际最大化之间进行权衡。对于较大的“C”值，如果决策函数能够更好地正确分类所有训练点，则可以接受较小的margin值。较低的“C”将鼓励更大的边际，因此一个更简单的决策函数，以训练准确性为代价。换句话说，' ' C ' '在SVM中充当一个正则化参数。
第一个图是关于一个简化分类问题的各种参数值的决策函数的可视化，该问题只涉及2个输入特征和2个可能的目标类别(二元分类)。请注意，对于包含更多特性或目标类的问题，这种绘图是不可能完成的。
第二幅图是分类器交叉验证准确性的热图，作为“C”和“gamma”的函数。为了便于演示，我们在本例中探索了一个相对较大的网格。在实践中，从:math: ' 10^{-3} '到:math: ' 10^3 '的对数网格通常就足够了。如果最佳参数位于网格的边界上，则可以在后续的搜索中向该方向扩展。
请注意，热图图有一个特殊的颜色条，其中点值接近表现最好的模型的评分值，以便于在眨眼之间很容易区分它们。
模型的行为对“伽马”参数非常敏感。如果' ' gamma ' '太大，则支持向量的影响区域半径等于支持向量本身，再多的正则化' ' C '都无法防止过拟合。
当' ' gamma ' '非常小的时候，模型就太受约束了，不能捕捉到数据的复杂性或“形状”。任何选定的支持向量的影响区域将包括整个训练集。结果模型的行为类似于线性模型，它有一组超平面，将两个类的任意一对的高密度中心分开。
对于中间值，我们可以在第二张图中看到，好的模型可以在' ' C ' '和' ' gamma ' '的对角线上找到。平滑的模型(较低的“gamma”值)可以通过增加正确分类每个点的重要性(较大的“C”值)而变得更加复杂，因此具有良好性能的模型的对角线。
最后，我们还可以观察到，对于' ' gamma ' ' '的一些中间值，当' ' ' C ' '变得非常大时，我们得到了同等性能的模型。这表明支持向量的集合不再改变。径向基核的半径是一种很好的结构正则化方法。进一步增加“C”并没有帮助，可能是因为没有更多的训练点违反(在边界内或错误分类)，或者至少没有找到更好的解决方案。分数相等时，使用较小的' ' C ' '值可能是有意义的，因为很高的' ' C ' '值通常会增加拟合时间。
另一方面，较低的“C”值通常会导致更多的支持向量，这可能会增加预测时间。因此，降低“' ' C ' '的值涉及到拟合时间和预测时间之间的权衡。
我们还应该注意到，分数的微小差异来自交叉验证过程的随机拆分。这些虚假的变化可以通过以计算时间为代价增加CV迭代“n次分割”的次数来消除。增加' ' C_range ' '和' ' gamma_range ' '步长，将提高超参数热图的分辨率。
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_iris
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import GridSearchCV


# Utility function to move the midpoint of a colormap to be around
# the values of interest.


class MidpointNormalize(Normalize):
    def __init__(self, vmin=None, vmax=None, midpoint=None, clip=False):
        self.midpoint = midpoint
        Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
        return np.ma.masked_array(np.interp(value, x, y))


# #############################################################################
# Load and prepare data set
#
# dataset for grid search


iris = load_iris()
X = iris.data
y = iris.target

# Dataset for decision function visualization: we only keep the first two
# features in X and sub-sample the dataset to keep only 2 classes and
# make it a binary classification problem.

X_2d = X[:, :2]
X_2d = X_2d[y > 0]
y_2d = y[y > 0]
y_2d -= 1

# It is usually a good idea to scale the data for SVM training.
# We are cheating a bit in this example in scaling all of the data,
# instead of fitting the transformation on the training set and
# just applying it on the test set.

scaler = StandardScaler()
X = scaler.fit_transform(X)
X_2d = scaler.fit_transform(X_2d)

# #############################################################################
# Train classifiers
#
# For an initial search, a logarithmic grid with basis
# 10 is often helpful. Using a basis of 2, a finer
# tuning can be achieved but at a much higher cost.

C_range = np.logspace(-2, 10, 13)
gamma_range = np.logspace(-9, 3, 13)
param_grid = dict(gamma=gamma_range, C=C_range)
cv = StratifiedShuffleSplit(n_splits=5, test_size=0.2, random_state=42)
grid = GridSearchCV(SVC(), param_grid=param_grid, cv=cv)
grid.fit(X, y)

print(
    "The best parameters are %s with a score of %0.2f"
    % (grid.best_params_, grid.best_score_)
)

# Now we need to fit a classifier for all parameters in the 2d version
# (we use a smaller set of parameters here because it takes a while to train)

C_2d_range = [1e-2, 1, 1e2]
gamma_2d_range = [1e-1, 1, 1e1]
classifiers = []
for C in C_2d_range:
    for gamma in gamma_2d_range:
        clf = SVC(C=C, gamma=gamma)
        clf.fit(X_2d, y_2d)
        classifiers.append((C, gamma, clf))

# #############################################################################
# Visualization
#
# draw visualization of parameter effects

plt.figure(figsize=(8, 6))
xx, yy = np.meshgrid(np.linspace(-3, 3, 200), np.linspace(-3, 3, 200))
for (k, (C, gamma, clf)) in enumerate(classifiers):
    # evaluate decision function in a grid
    Z = clf.decision_function(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    # visualize decision function for these parameters
    plt.subplot(len(C_2d_range), len(gamma_2d_range), k + 1)
    plt.title("gamma=10^%d, C=10^%d" % (np.log10(gamma), np.log10(C)), size="medium")

    # visualize parameter's effect on decision function
    plt.pcolormesh(xx, yy, -Z, cmap=plt.cm.RdBu, shading='auto')
    plt.scatter(X_2d[:, 0], X_2d[:, 1], c=y_2d, cmap=plt.cm.RdBu_r, edgecolors="k")
    plt.xticks(())
    plt.yticks(())
    plt.axis("tight")

scores = grid.cv_results_["mean_test_score"].reshape(len(C_range), len(gamma_range))

# Draw heatmap of the validation accuracy as a function of gamma and C
#
# The score are encoded as colors with the hot colormap which varies from dark
# red to bright yellow. As the most interesting scores are all located in the
# 0.92 to 0.97 range we use a custom normalizer to set the mid-point to 0.92 so
# as to make it easier to visualize the small variations of score values in the
# interesting range while not brutally collapsing all the low score values to
# the same color.

plt.figure(figsize=(8, 6))
plt.subplots_adjust(left=0.2, right=0.95, bottom=0.15, top=0.95)
plt.imshow(
    scores,
    interpolation="nearest",
    cmap=plt.cm.hot,
    norm=MidpointNormalize(vmin=0.2, midpoint=0.92),
)
plt.xlabel("gamma")
plt.ylabel("C")
plt.colorbar()
plt.xticks(np.arange(len(gamma_range)), gamma_range, rotation=45)
plt.yticks(np.arange(len(C_range)), C_range)
plt.title("Validation accuracy")
plt.show()
