# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *


"""
上轨=昨日最高点；
下轨=昨日最低点；
止损=今日开盘价;
如果没有持仓，且现价大于了昨天最高价做多，小于昨天最低价做空。
如果有多头持仓，当价格跌破了开盘价止损。
如果有空头持仓，当价格上涨超过开盘价止损。
选取 进行了回测。
注意： 
1：为回测方便，本策略使用了on_bar的一分钟来计算，实盘中可能需要使用on_tick。
2：实盘中，如果在收盘的那一根bar或tick触发交易信号，需要自行处理，实盘可能不会成交。
"""


def init(context):
    # 设置标的
    context.symbol = 'SHFE.rb2010'
    # 订阅一分钟线
    subscribe(symbols = context.symbol,frequency = '60s',count = 1)
    # 记录开仓次数，保证一天只开仓一次
    context.count = 0
    # 记录当前时间
    time = context.now.strftime('%H:%M:%S')
    # 如果当前时间点是交易时间段，则直接执行algo获取历史数据，以防直接进入on_bar()导致context.history_data未定义
    if '09:00:00' < time < '15:00:00' or '21:00:00' < time < '23:00:00':
        algo(context)

    # 如果是非交易时间段，等到上午9点或晚上21点再执行algo()
    schedule(schedule_func=algo, date_rule='1d', time_rule='09:00:00')
    schedule(schedule_func=algo, date_rule='1d', time_rule='21:00:00')


def algo(context):
    # 获取历史的n条信息
    context.history_data = history_n(symbol=context.symbol, frequency='1d', end_time=context.now,
                                     fields='symbol,open,high,low', count=2, df=True)

def on_bar(context,bars):
    # 取出订阅的一分钟bar
    bar = bars[0]

    # 提取数据
    data = context.history_data

    # 现有持仓情况
    position_long = context.account().position(symbol=context.symbol, side=PositionSide_Long)
    position_short = context.account().position(symbol=context.symbol, side=PositionSide_Short)

    # 如果是回测模式
    if context.mode == 2:
        # 开盘价直接在data最后一个数据里取到,前一交易日的最高和最低价为history_data里面的倒数第二条中取到
        open = data.loc[1, 'open']
        high = data.loc[0, 'high']
        low = data.loc[0, 'low']

    # 如果是实时模式
    else:
        # 开盘价通过current取到
        open = current(context.symbol)[0]['open']
        # 实时模式不会返回当天的数据，所以history_data里面的最后一条数据是前一交易日的数据
        high = data.loc[-1, 'high']
        low = data.loc[-1, 'low']

    # 交易逻辑部分
    if position_long:  # 多头持仓小于开盘价止损。
        if bar.close < open:
            order_volume(symbol=context.symbol, volume=1, side=OrderSide_Sell,
                         order_type=OrderType_Market, position_effect=PositionEffect_Close)
            print('以市价单平多仓')

    elif position_short:# 空头持仓大于开盘价止损。
        if bar.close > open:
            order_volume(symbol=context.symbol, volume=1, side=OrderSide_Buy,
                         order_type=OrderType_Market, position_effect=PositionEffect_Close)
            print('以市价单平空仓')

    else:  # 没有持仓
        if bar.close > high and not context.count:  # 当前的最新价大于了前一天的最高价
            # 开多
            order_volume(symbol=context.symbol, volume=1, side=OrderSide_Buy,
                         order_type=OrderType_Market, position_effect=PositionEffect_Open)
            print('以市价单开多仓')
            context.count = 1
        elif bar.close < low and not context.count:  # 当前最新价小于了前一天的最低价
            # 开空
            order_volume(symbol=context.symbol, volume=1, side=OrderSide_Sell,
                         order_type=OrderType_Market, position_effect=PositionEffect_Open)
            print('以市价单开空仓')
            context.count = 1

    # 每天收盘前一分钟平仓
    if context.now.hour == 14 and context.now.minute == 59:
        order_close_all()
        print('全部平仓')
        context.count = 0
            

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
        backtest_start_time='2020-01-01 15:00:00',
        backtest_end_time='2020-09-01 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=100000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)
