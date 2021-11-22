# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
import talib
import time

'''
8.  本策略以DCE.i1801为交易标的，根据其一分钟(即60s频度）bar数据建立双均线模型，
9.  短周期为30，长周期为60，当短期均线由上向下穿越长期均线时做空，
10.  当短期均线由下向上穿越长期均线时做多,每次开仓前先平掉所持仓位，再开仓。
11.  回测数据为:DCE.i1801的60s频度bar数据
12.  回测时间为:2017-09-01 09:00:00到2017-09-30 15:00:00
13.  '''


def init(context):
    context.FAST = 30  # 短周期
    context.SLOW = 60  # 长周期
    context.symbol = 'DCE.i1801'  # 订阅&交易标的
    context.period = context.SLOW + 1  # 订阅数据滑窗长度
    subscribe(context.symbol, '60s', count=context.period)  # 订阅行情


def on_bar(context, bars):
    print(bars[0].bob)
    # 获取数据
    prices = context.data('DCE.i1801', '60s', context.period, fields='close')
    # 计算长短周期均线
    fast_avg = talib.SMA(prices.values.reshape(context.period), context.FAST)
    slow_avg = talib.SMA(prices.values.reshape(context.period), context.SLOW)

    # 均线下穿，做空
    if slow_avg[-2] < fast_avg[-2] and slow_avg[-1] >= fast_avg[-1]:
        # 平多仓
        order_target_percent(symbol=context.symbol, percent=0, position_side=1, order_type=2)
        # 开空仓
    order_target_percent(symbol=context.symbol, percent=0.1, position_side=2, order_type=2)

    # 均线上穿，做多
    if fast_avg[-2] < slow_avg[-2] and fast_avg[-1] >= slow_avg[-1]:
        # 平空仓
        order_target_percent(symbol=context.symbol, percent=0, position_side=2, order_type=2)
        # 开多仓
        order_target_percent(symbol=context.symbol, percent=0.1, position_side=1, order_type=2)


def on_execution_report(context, execrpt):
    # 打印委托执行回报
    print(execrpt)


if __name__ == '__main__':
    '''
         strategy_id策略ID,由系统生成
         filename文件名,请与本文件名保持一致
         mode实时模式:MODE_LIVE回测模式:MODE_BACKTEST
         token绑定计算机的ID,可在系统设置-密钥管理中生成
         backtest_start_time回测开始时间
         backtest_end_time回测结束时间
         backtest_adjust股票复权方式不复权:ADJUST_NONE前复权:ADJUST_PREV后复权:ADJUST_POST
         backtest_initial_cash回测初始资金
         backtest_commission_ratio回测佣金比例
         backtest_slippage_ratio回测滑点比例
         '''
    run(strategy_id='strategy_id',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='token_id',
        backtest_start_time='2017-09-01 09:00:00',
        backtest_end_time='2017-09-30 15:00:00',
        backtest_adjust=ADJUST_NONE,
        backtest_initial_cash=10000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)
