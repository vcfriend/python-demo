# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import numpy as np
import pandas as pd
from gm.api import *

'''
以短期为例：20日线
第一步：获取历史数据，计算唐奇安通道和ATR
第二步：当突破唐奇安通道时，开仓。
第三步：计算加仓和止损信号。
'''


def init(context):
    # 设置计算唐奇安通道的参数
    context.n = 20
    # 设置合约标的
    context.symbol = 'DCE.i2012'
    # 设置交易最大资金比率
    context.ratio = 0.8
    # 订阅数据
    subscribe(symbols=context.symbol, frequency='60s', count=2)
    # 获取当前时间
    time = context.now.strftime('%H:%M:%S')
    # 如果策略执行时间点是交易时间段，则直接执行algo定义atr等参数，以防直接进入on_bar()导致atr等未定义
    if '09:00:00' < time < '15:00:00' or '21:00:00' < time < '23:00:00':
        algo(context)
    # 如果是交易时间段，等到开盘时间确保进入algo()
    schedule(schedule_func=algo, date_rule='1d', time_rule='09:00:00')
    schedule(schedule_func=algo, date_rule='1d', time_rule='21:00:00')


def algo(context):
    # 计算通道的数据:当日最低、最高、上一交易日收盘
    # 注：由于talib库计算ATR的结果与公式求得的结果不符，所以这里利用公式计算ATR
    # 如果是回测模式,当天的数据直接用history取到
    if context.mode == 2:
        data = history_n(symbol=context.symbol, frequency='1d', count=context.n + 1, end_time=context.now,
                         fields='close,high,low,bob', df=True)  # 计算ATR
        tr_list = []
        for i in range(0, len(data) - 1):
            tr = max((data['high'].iloc[i] - data['low'].iloc[i]),
                     data['close'].shift(-1).iloc[i] - data['high'].iloc[i],
                     data['close'].shift(-1).iloc[i] - data['low'].iloc[i])
            tr_list.append(tr)
        context.atr = int(np.floor(np.mean(tr_list)))
        context.atr_half = int(np.floor(0.5 * context.atr))
        # 计算唐奇安通道
        context.don_open = np.max(data['high'].values[-context.n:])
        context.don_close = np.min(data['low'].values[-context.n:])

    # 如果是实时模式，当天的数据需要用current取到
    if context.mode == 1:
        data = history_n(symbol=context.symbol, frequency='1d', count=context.n, end_time=context.now,
                         fields='close,high,low',
                         df=True)  # 计算ATR
        current_data = current(symbols=context.symbol)  # 最新一个交易日的最高、最低
        tr_list = []
        for i in range(1, len(data)):
            tr = max((data['high'].iloc[i] - data['low'].iloc[i]),
                     data['close'].shift(-1).iloc[i] - data['high'].iloc[i],
                     data['close'].shift(-1).iloc[i] - data['low'].iloc[i])
            tr_list.append(tr)
        # 把最新一期tr加入列表中
        tr_new = max((current_data[0]['high'] - current_data[0]['low']),
                     data['close'].iloc[-1] - current_data[0]['high'],
                     data['close'].iloc[-1] - current_data[0]['low'])
        tr_list.append(tr_new)
        context.atr = int(np.floor(np.mean(tr_list)))
        context.atr_half = int(np.floor(0.5 * context.atr))
        # 计算唐奇安通道
        context.don_open = np.max(data['high'].values[-context.n:])
        context.don_close = np.min(data['low'].values[-context.n:])

    # 计算加仓点和止损点
    context.long_add_point = context.don_open + context.atr_half
    context.long_stop_loss = context.don_open - context.atr_half
    context.short_add_point = context.don_close - context.atr_half
    context.short_stop_loss = context.don_close + context.atr_half


def on_bar(context, bars):
    # 提取数据
    symbol = bars[0]['symbol']
    recent_data = context.data(symbol=context.symbol, frequency='60s', count=2, fields='close,high,low')
    close = recent_data['close'].values[-1]

    # 账户仓位情况
    position_long = context.account().position(symbol=symbol, side=PositionSide_Long)
    position_short = context.account().position(symbol=symbol, side=PositionSide_Short)

    # 当无持仓时
    if not position_long and not position_short:
        # 如果向上突破唐奇安通道，则开多
        if close > context.don_open:
            order_volume(symbol=symbol, side=OrderSide_Buy, volume=context.atr, order_type=OrderType_Market,
                         position_effect=PositionEffect_Open)
            print('开多仓atr')
        # 如果向下突破唐奇安通道，则开空
        if close < context.don_close:
            order_volume(symbol=symbol, side=OrderSide_Sell, volume=context.atr, order_type=OrderType_Market,
                         position_effect=PositionEffect_Open)
            print('开空仓atr')

    # 有持仓时
    # 持多仓，继续突破（加仓）
    if position_long:
        # 当突破1/2atr时加仓
        if close > context.long_add_point:
            order_volume(symbol=symbol, volume=context.atr_half, side=OrderSide_Buy, order_type=OrderType_Market,
                         position_effect=PositionEffect_Open)
            print('继续加仓0.5atr')
            context.long_add_point += context.atr_half
            context.long_stop_loss += context.atr_half
        # 持多仓，止损位计算
        if close < context.long_stop_loss:
            volume_hold = position_long['volume']
            if volume_hold >= context.atr_half:
                order_volume(symbol=symbol, volume=context.atr_half, side=OrderSide_Sell, order_type=OrderType_Market,
                             position_effect=PositionEffect_Close)
            else:
                order_volume(symbol=symbol, volume=volume_hold, side=OrderSide_Sell, order_type=OrderType_Market,
                             position_effect=PositionEffect_Close)
            print('平多仓0.5atr')
            context.long_add_point -= context.atr_half
            context.long_stop_loss -= context.atr_half

    # 持空仓，继续突破（加仓）
    if position_short:
        # 当跌破加仓点时加仓
        if close < context.short_add_point:
            order_volume(symbol=symbol, volume=context.atr_half, side=OrderSide_Sell, order_type=OrderType_Market,
                         position_effect=PositionEffect_Open)
            print('继续加仓0.5atr')
            context.short_add_point -= context.atr_half
            context.short_stop_loss -= context.atr_half
        # 持多仓，止损位计算
        if close > context.short_stop_loss:
            volume_hold = position_short['volume']
            if volume_hold >= context.atr_half:
                order_volume(symbol=symbol, volume=context.atr_half, side=OrderSide_Buy, order_type=OrderType_Market,
                             position_effect=PositionEffect_Close)
            else:
                order_volume(symbol=symbol, volume=volume_hold, side=OrderSide_Buy, order_type=OrderType_Market,
                             position_effect=PositionEffect_Close)
            print('平空仓0.5atr')
            context.short_add_point += context.atr_half
            context.short_stop_loss += context.atr_half


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
        token='{{token}}',
        backtest_start_time='2020-02-15 09:15:00',
        backtest_end_time='2020-09-01 15:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=1000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)
