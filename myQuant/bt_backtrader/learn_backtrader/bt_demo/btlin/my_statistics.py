from datetime import datetime


class My_Statistics():
    """策略统计,成交记录"""
    # 记录每笔交易的成交与账户持仓等信息
    trade_record = {
        'datetime': [],  # 记录每笔交易发生的时间
        '订单': [],  # 订单类型: 多,空,净
        '执行': [],  # 执行操作: 开,平,平令,平昨
        '交易量': [],  # 发送订单的交易数量
        '成交量': [],  # 已成交的数量
        '多头持仓': [],  # 多头持仓数量
        '空头持仓': [],  # 空头持仓数量
        '成交价': [],  # 开仓时成交价为开仓价, 平仓时成交价为平仓价
        '持仓均价': [],  # 账户头寸持仓均价
        '平仓盈亏%': [],  # 平仓时统计盈亏比率
        '浮动盈亏%': [],  # 开仓时浮动盈亏比率
        '收益率%': [],  # 累计收益率
        '保证金%': [],  # 保证金率
        '仓位%': [],  # 保证金占用总资金百分比的持仓仓位
        '回撤%': [],  # 账户金额创新高后的回撤率
        '帐户金额': [],  # 账户金额
        '浮动盈亏': [],  # 开仓时浮动盈亏>0为盈利,<0为亏损
        '平仓盈亏': [],  # 平仓时统计盈亏>0为盈利,<0为亏损
        '手续费': [],  # 交易手续费
    }
    # 时间段内的统计分析
    analysis_date = {
        'date': [],  # 时间段 日,月,年
        '收益率%': [],  # 收益率
        '胜率%': [],  # 胜率
        '手续费%': [],  # 交易费/(利润扣除手续费的净盈亏)
        '盈亏比': [],  # 盈亏比=平均盈利/平均亏损
        '回撤%': [],  # 账户金额创新高后的回撤率
        '交易次数': [],  # 交易次数
        '净利润': [],  # 净利润
        '总盈利': [],  # 总盈利
        '总亏损': [],  # 总亏损
        '平均盈利': [],  # 平均盈利
        '平均亏损': [],  # 平均亏损
        '手续费': [],  # 交易手续费
    }
    datetime_begin: datetime = None  # 第一笔交易开始时间
    datetime_end: datetime = None  # 最后一笔交易开始时间
    gross_profit = 0.0  # 总盈利=策略盈利总额（未扣除手续费）
    cumulative_return = 0.0  # 累计收益率
    gross_loss = 0.0  # 总亏损=策略亏损总额（未扣除手续费）
    gross_num_trade = 0  # 总交易次数
    num_trade_win = 0  # 盈利交易次数
    num_trade_loss = 0  # 亏损交易次数
    max_num_seq_loss = 0  # 最大连续亏损次数
    avg_num_seq_loss = 0  # 平均连续亏损次数
    max_num_seq_win = 0  # 最大连续盈利次数
    avg_num_seq_win = 0  # 平均连续盈利次数
    percent_win = 0  # 胜率=盈利交易占总交易次数的比例
    payoff_rate = 0.0  # 盈亏比=平均盈利/平均亏损
    avg_payoff = 0.0  # 平均盈亏 = 净利润 / 交易次数.
    avg_win = 0.0  # 平均盈利=总盈利/盈利交易次数
    avg_loss = 0.0  # 平均亏损=总亏损/亏损交易次数
    comm_profit_net = 0.0  # 交易费/(利润扣除手续费的净盈亏)
    max_drawdown = 0.0  # 最大回撤
    sharp_rate = 0.0  # 夏普率

    pass