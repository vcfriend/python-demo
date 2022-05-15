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
            comm = abs(size) * price * self.p.commission * self.p.mult
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

    # """设置手续费"""
    def set_commission_info(cerebro, cont_id: str):
        """设置手续费"""
        # # <editor-fold desc="折叠代码:交易手续费设置一">
        # cerebro.broker.setcommission(
        #     # 交易手续费，根据margin取值情况区分是百分比手续费还是固定手续费
        #     commission=0.0015,
        #     # commission=4,
        #     # 期货保证金，决定着交易费用的类型,只有在stocklike=False时起作用
        #     margin=0,
        #     # 乘数，盈亏会按该乘数进行放大
        #     mult=10.0,
        #     # 交易费用计算方式，取值有：
        #     # 1.CommInfoBase.COMM_PERC 百分比费用
        #     # 2.CommInfoBase.COMM_FIXED 固定费用
        #     # 3.None 根据 margin 取值来确定类型
        #     commtype=bt.CommInfoBase.COMM_PERC,
        #     # 当交易费用处于百分比模式下时，commission 是否为 % 形式
        #     # True，表示不以 % 为单位，0.XX 形式；False，表示以 % 为单位，XX% 形式
        #     percabs=True,
        #     # 是否为股票模式，该模式通常由margin和commtype参数决定
        #     # margin=None或COMM_PERC模式时，就会stocklike=True，对应股票手续费；
        #     # margin设置了取值或COMM_FIXED模式时,就会stocklike=False，对应期货手续费
        #     stocklike=False,
        #     # 计算持有的空头头寸的年化利息
        #     # days * price * abs(size) * (interest / 365)
        #     interest=0.0,
        #     # 计算持有的多头头寸的年化利息
        #     interest_long=False,
        #     # 杠杆比率，交易时按该杠杆调整所需现金
        #     leverage=1.0,
        #     # 自动计算保证金
        #     # 如果 False, 则通过margin参数确定保证金
        #     # 如果automargin<0, 通过mult*price确定保证金
        #     # 如果automargin>0, 如果 automargin*price确定保证金 automargin=mult*margin
        #     automargin=10 * 0.13,
        #     # 交易费用设置作用的数据集(也就是作用的标的)
        #     # 如果取值为None，则默认作用于所有数据集(也就是作用于所有assets)
        #     name=None
        # )
        # # </editor-fold>
        pass
        # <editor-fold desc="折叠代码:交易手续费设置方式二">
        # from bt_demo.btlin.my_strategy_config import MyCommission  # 自定义合约信息
        comm = {
            'ZJIF': MyCommission(commtype=bt.CommInfoBase.COMM_PERC, commission=0.00046, margin_rate=0.23, mult=300.0),  # 股指合约信息 平今仓为万分之4.6
            'SQRB': MyCommission(commtype=bt.CommInfoBase.COMM_PERC, commission=0.00015, margin_rate=0.13, mult=10.0),  # 螺纹钢合约信息 万分之1.5
            'SQCU': MyCommission(commtype=bt.CommInfoBase.COMM_PERC, commission=0.00015, margin_rate=0.14, mult=5.0),  # 沪铜合约信息
            'DQC': MyCommission(commtype=bt.CommInfoBase.COMM_FIXED, commission=2.4, margin_rate=0.10, mult=10.0),  # 玉米合约信息
            'ZQCF': MyCommission(commtype=bt.CommInfoBase.COMM_FIXED, commission=4.0, margin_rate=0.11, mult=5.0),  # 棉花合约信息

        }
        # 添加进 broker
        cerebro.broker.addcommissioninfo(comm[cont_id], name=None)  # name 用于指定该交易费用函数适用的标的,未指定将适用所有标的
        # </editor-fold>
        pass
