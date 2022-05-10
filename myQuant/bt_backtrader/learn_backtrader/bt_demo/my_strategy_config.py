import backtrader as bt


# 在继承 CommInfoBase 基础类的基础上自定义交易费用
class MyCommission(bt.CommInfoBase):
    # 对应 setcommission 中介绍的那些参数，也可以增添新的全局参数
    params = (
        ('stocklike', False),  # False期货模式
        ('commtype', bt.CommInfoBase.COMM_PERC),  # 使用百分比费用模式
        ('percabs', True),  # commission 不以 % 为单位
        ('leverage', 1.0),  # 杠杆比率，交易时按该杠杆调整所需现金
        ('margin_rate', False),  # 期货保证金比率
        ('commission', 0.0),  # 交易手续费，根据margin取值情况区分是百分比手续费还是固定手续费
        ('mult', 1.0),  # 合约乘数，盈亏会按该乘数进行放大
        ('margin', None),  # 期货保证金，决定着交易费用的类型,只有在 stocklike=False 和 automargin=False时起作用
    )

    # 自定义费用计算公式
    def _getcommission(self, size, price, pseudoexec):
        comm = 0.0
        if self.p.commtype == bt.CommInfoBase.COMM_PERC:  # 百分比手续费
            comm = abs(size) * price * self.p.commission
        elif self.p.commtype == bt.CommInfoBase.COMM_FIXED:  # 固定手续费
            comm = abs(size) * self.p.commission
        return comm

    # 自定义保证金计算方式
    def get_margin(self, price):
        """计算保证金"""
        value = 0.0
        if not self.p.margin_rate:
            value = self.p.margin
        elif self.p.margin_rate < 0:
            value = price * self.p.mult
        elif self.p.margin_rate > 0:
            value = price * self.p.mult * self.p.margin_rate  # int/float expected
        self.p.margin = value  # 设置保证金
        return value
