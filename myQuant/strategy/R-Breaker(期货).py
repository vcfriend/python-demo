# coding=utf-8
from __future__ import print_function, absolute_import
import pandas as pd
from gm.api import *
from datetime import datetime, timedelta

"""
R-Breaker是一种短线日内交易策略
根据前一个交易日的收盘价、最高价和最低价数据通过一定方式计算出六个价位，从大到小依次为：
突破买入价、观察卖出价、反转卖出价、反转买入、观察买入价、突破卖出价。以此来形成当前交易
日盘中交易的触发条件。
追踪盘中价格走势，实时判断触发条件。具体条件如下：
突破
在空仓条件下，如果盘中价格超过突破买入价，则采取趋势策略，即在该点位开仓做多。
在空仓条件下，如果盘中价格跌破突破卖出价，则采取趋势策略，即在该点位开仓做空。
反转
持多单，当日内最高价超过观察卖出价后，盘中价格出现回落，且进一步跌破反转卖出价构成的支撑线时，采取反转策略，即在该点位反手做空。
持空单，当日内最低价低于观察买入价后，盘中价格出现反弹，且进一步超过反转买入价构成的阻力线时，采取反转策略，即在该点位反手做多。
设定止损条件。当亏损达到设定值后，平仓。
注意： 
1：为回测方便，本策略使用了on_bar的一分钟来计算，实盘中可能需要使用on_tick。
2：实盘中，如果在收盘的那一根bar或tick触发交易信号，需要自行处理，实盘可能不会成交。
3：本策略使用在15点收盘时全平的方式来处理不持有隔夜单的情况，实际使用中15点是无法平仓的。
"""

def init(context):
    # 设置交易品种
    context.symbol = 'SHFE.ag'

    # 设置止损点数
    context.stopLossPrice = 50

    # 获取前一交易日的主力合约
    startDate = get_previous_trading_date(exchange='SHFE', date=context.now.date())
    continuous_contract = get_continuous_contracts(context.symbol, startDate, startDate)
    context.mainContract = continuous_contract[0]['symbol']

    # 获取当前时间
    time = context.now.strftime('%H:%M:%S')

    # 如果当前时间是非交易时间段，则直接执行algo,以防直接进入on_bar()导致context.bBreak等未定义
    if '09:00:00' < time < '15:00:00' or '21:00:00' < time < '23:00:00':
        algo(context)

    # 如果是交易时间段，等到开盘时间确保进入algo()
    schedule(schedule_func=algo, date_rule='1d', time_rule='09:00:00')
    schedule(schedule_func=algo, date_rule='1d', time_rule='21:00:00')

    # 订阅行情
    subscribe(continuous_contract[0]['symbol'], frequency='60s', count=1)


def algo(context):
    # 检查主力和约，发生变化则更换订阅
    # 由于主力合约在盘后才公布，为了防止未来函数，选择上一交易日的主力合约。
    startDate = get_previous_trading_date(exchange='SHFE', date=context.now.date())
    contractInfo = get_continuous_contracts(context.symbol, startDate, startDate)

    if context.mainContract != contractInfo[0]['symbol']:
        context.mainContract = contractInfo[0]['symbol']
        subscribe(context.mainContract, frequency='60s', count=1, unsubscribe_previous=True)

    # 获取历史数据
    data = history_n(symbol=context.mainContract, frequency='1d',
                     end_time=context.now, fields='high,low,open,symbol,close', count=2, df=True)

    high = data['high'].iloc[0]  # 前一日的最高价
    low = data['low'].iloc[0]  # 前一日的最低价
    close = data['close'].iloc[0]  # 前一日的收盘价
    pivot = (high + low + close) / 3  # 枢轴点

    context.bBreak = high + 2 * (pivot - low)  # 突破买入价
    context.sSetup = pivot + (high - low)  # 观察卖出价
    context.sEnter = 2 * pivot - low  # 反转卖出价
    context.bEnter = 2 * pivot - high  # 反转买入价
    context.bSetup = pivot - (high - low)  # 观察买入价
    context.sBreak = low - 2 * (high - pivot)  # 突破卖出价
    context.data = data


def on_bar(context, bars):
    # 获取止损价
    STOP_LOSS_PRICE = context.stopLossPrice
    # 设置参数
    bBreak = context.bBreak
    sSetup = context.sSetup
    sEnter = context.sEnter
    bEnter = context.bEnter
    bSetup = context.bSetup
    sBreak = context.sBreak
    data = context.data

    # 获取现有持仓
    position_long = context.account().position(symbol=context.mainContract, side=PositionSide_Long)
    position_short = context.account().position(symbol=context.mainContract, side=PositionSide_Short)

    # 突破策略:
    if not position_long and not position_short:  # 空仓条件下
        if bars[0].close > bBreak:
            # 在空仓的情况下，如果盘中价格超过突破买入价，则采取趋势策略，即在该点位开仓做多
            order_volume(symbol=context.mainContract, volume=10, side=OrderSide_Buy,
                         order_type=OrderType_Market, position_effect=PositionEffect_Open)  # 做多
            print("空仓,盘中价格超过突破买入价: 开仓做多")
            context.open_position_price = bars[0].close

        elif bars[0].close < sBreak:
            # 在空仓的情况下，如果盘中价格跌破突破卖出价，则采取趋势策略，即在该点位开仓做空
            order_volume(symbol=context.mainContract, volume=10, side=OrderSide_Sell,
                         order_type=OrderType_Market, position_effect=PositionEffect_Open)  # 做空
            print("空仓,盘中价格跌破突破卖出价: 开仓做空")

            context.open_position_price = bars[0].close

    # 设置止损条件
    else:  # 有持仓时
        # 开仓价与当前行情价之差大于止损点则止损
        if (position_long and context.open_position_price - bars[0].close >= STOP_LOSS_PRICE) or \
                (position_short and bars[0].close - context.open_position_price >= STOP_LOSS_PRICE):
            print('达到止损点，全部平仓')
            order_close_all()  # 平仓

        # 反转策略:
        if position_long:  # 多仓条件下
            if data.high.iloc[1] > sSetup and bars[0].close < sEnter:
                # 多头持仓,当日内最高价超过观察卖出价后，
                # 盘中价格出现回落，且进一步跌破反转卖出价构成的支撑线时，
                # 采取反转策略，即在该点位反手做空
                order_close_all()  # 平仓
                order_volume(symbol=context.mainContract, volume=10, side=OrderSide_Sell,
                             order_type=OrderType_Market, position_effect=PositionEffect_Open)  # 做空
                print("多头持仓,当日内最高价超过观察卖出价后跌破反转卖出价: 反手做空")
                context.open_position_price = bars[0].close

        elif position_short:  # 空头持仓
            if data.low.iloc[1] < bSetup and bars[0].close > bEnter:
                # 空头持仓，当日内最低价低于观察买入价后，
                # 盘中价格出现反弹，且进一步超过反转买入价构成的阻力线时，
                # 采取反转策略，即在该点位反手做多
                order_close_all()  # 平仓
                order_volume(symbol=context.mainContract, volume=10, side=OrderSide_Buy,
                             order_type=OrderType_Market, position_effect=PositionEffect_Open)  # 做多
                print("空头持仓,当日最低价低于观察买入价后超过反转买入价: 反手做多")
                context.open_position_price = bars[0].close

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
        backtest_start_time='2019-10-1 15:00:00',
        backtest_end_time='2020-04-16 15:00:00',
        backtest_initial_cash=1000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)