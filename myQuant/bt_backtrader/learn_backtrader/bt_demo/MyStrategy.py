import os, sys
import time
import backtrader as bt
import logging
import quantstats
import argparse
import pandas as pd
import numpy as np
from enum import Enum
from datetime import datetime
from my_tradeanalyzer import My_TradeAnalyzer  # 自定义分析器


class TargetType(Enum):
    """枚举开仓类型"""
    T_SIZE = "数量"  # 成交量
    T_VALUE = "金额"  # 目标金额
    T_PERCENT = "百分比"  # 百分比


# G_FILE_PATH = "datas\\ZJIF13-5m-20100416-20220427.csv"
# G_DT_START, G_DT_END = '2013-01-01', '2022-02-01'
# G_FILE_PATH = "datas\\ZQCF13-5m-20121224-20220415.csv"
# G_DT_START, G_DT_END = '2013-01-01', '2014-02-01'
# G_FILE_PATH = "datas\\SQRB13-5m-20121224-20220330.csv"
G_FILE_PATH = "datas\\SQRBOC-5m-20090327-20211231.csv"
G_DT_START, G_DT_END = '2009-04-01', '2013-02-01'

G_DT_DTFORMAT = '%Y-%m-%d %H:%M:%S'
G_COMM = 'comm_' + G_FILE_PATH.split('\\')[1][:4].lower()  # 合约信息,提前预设好 保证金,手续费率,合约乘数等
G_DT_TIMEFRAME = 'minutes'  # 重采样更大时间周期 choices=['minutes', 'daily', 'weekly', 'monthly']
G_DT_COMPRESSION = 5  # 合成bar的周期数
G_INI_CASH = 10000 * 10  # 初始金额
G_PLOT = False  # 是否绘图,可提供绘图参数:'style="candle"'
G_QUANTSTATS = True  # 是否使用 quantstats 分析测试结果
G_P_LOG_FILE = False  # 是否输出日志到文件
G_P_LOG_PRINT = 0  # 是否输出日志到控制台
G_OPTS = False  # 是否参数调优
G_P_PW = [8, False, 2, 10, 1]  # 参数[默认值,是否优化,最小值,最大值,步长]
G_P_PL = [8, False, 2, 10, 1]  # 参数[默认值,是否优化,最小值,最大值,步长]
G_P_PWL = [10, False, 2, 5, 1]  # 参数[默认值,是否优化,最小值,最大值,步长]
G_P_OJK = [1, False, 1, 3, 1]  # 参数[默认值,是否优化,最小值,最大值,步长]
G_P_PO = [0, False, 0, 5, 1]  # 参数[默认值,是否优化,最小值,最大值,步长]
G_P_PP = [0, False, 0, 5, 1]  # 参数[默认值,是否优化,最小值,最大值,步长]
G_P_KPR = [False, 4100, 3400, 1800, 6000]  # 关键价格[是否启用, 价格1, 价格2]
G_P_PARAM = {
    'pw': (range(G_P_PW[2], G_P_PW[3], G_P_PW[4]) if G_OPTS and G_P_PW[1] else G_P_PW[0]),
    'pl': (range(G_P_PL[2], G_P_PL[3], G_P_PL[4]) if G_OPTS and G_P_PL[1] else G_P_PL[0]),
    # 'pwl': (range(G_P_PWL[2], G_P_PWL[3], G_P_PWL[4]) if G_OPTS and G_P_PWL[1] else G_P_PWL[0]),
    # 'ojk': (range(G_P_OJK[2], G_P_OJK[3], G_P_OJK[4]) if G_OPTS and G_P_OJK[1] else G_P_OJK[0]),
    # 'po': (range(G_P_PO[2], G_P_PO[3], G_P_PO[4]) if G_OPTS and G_P_PO[1] else G_P_PO[0]),
    # 'pp': (range(G_P_PP[2], G_P_PP[3], G_P_PP[4]) if G_OPTS and G_P_PP[1] else G_P_PP[0]),
    # 'kpr': G_P_KPR[1:] if G_P_KPR[0] else None,

}


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for Order Target')

    parser.add_argument('--data', required=False,
                        default=G_FILE_PATH,
                        help='Specific data to be read in')
    parser.add_argument('--dtformat', required=False, default=G_DT_DTFORMAT,
                        help='Ending date in data datetime format')
    parser.add_argument('--fromdate', required=False, default=G_DT_START,
                        help='Starting date in `dtformat` format')
    parser.add_argument('--todate', required=False, default=G_DT_END,
                        help='Ending date in `dtformat` format')
    parser.add_argument('--timeframe', required=False, default=G_DT_TIMEFRAME,
                        choices=['minutes', 'daily', 'weekly', 'monthly'],
                        help='重新采样到的时间范围')
    parser.add_argument('--compression', required=False, type=int, default=G_DT_COMPRESSION, help='将 n 条压缩为 1, 最小周期为原数据周期')
    parser.add_argument('--kpr', required=False, type=list, default=G_P_PARAM['kpr'] if 'kpr' in G_P_PARAM else None, help='当穿越关键价格后加仓限制，列表类型 [price1, price2]'),
    parser.add_argument('--pwl', required=False, type=list, default=G_P_PARAM['pwl'] if 'pwl' in G_P_PARAM else None, help='--pwl 盈亏千分比'),
    parser.add_argument('--pw', required=False, type=list, default=G_P_PARAM['pw'] if 'pw' in G_P_PARAM else None, help='--pw 盈利千分比'),
    parser.add_argument('--pl', required=False, type=list, default=G_P_PARAM['pl'] if 'pl' in G_P_PARAM else None, help='--pl 亏损千分比'),
    parser.add_argument('--ojk', required=False, type=list, default=G_P_PARAM['ojk'] if 'ojk' in G_P_PARAM else None, help='--ojk 订单间隔bar周期数'),
    parser.add_argument('--opts', required=False, type=bool, default=G_OPTS, help='是否策略优化')
    parser.add_argument('--quantstats', required=False, type=int, default=G_QUANTSTATS, help='是否使用 quantstats 分析测试结果')
    parser.add_argument('--maxcpus', '-m', type=int, required=False, default=15, help=('Number of CPUs to use in the optimization'
                                                                                       '\n  - 0 (default): 使用所有可用的 CPU\n   - 1 -> n: 使用尽可能多的指定\n'))
    parser.add_argument('--no-optdatas', action='store_true', required=False, help='优化中不优化数据预加载')
    parser.add_argument('--no-optreturn', action='store_true', required=False,
                        help='不要优化返回值以节省时间,这避免了回传大量生成的数据，例如指标在回溯测试期间生成的值')

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const=True, default=G_PLOT,
                        help=('绘制应用传递的任何 kwargs 的读取数据\n'
                              '\n''例如:\n''\n''  --plot style="candle" (to plot candles)\n'))
    parser.add_argument("-f", "--file", default="file")  # 接收这个-f参数
    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


def runstrat(args=None):
    global DT_RESULT_ONE, DT_RESULTS_OPT, G_INI_CASH  # 申明要使用全局变量
    strats = None
    result_one = None
    results_opt = None

    args = parse_args(args)
    kwargs = dict()  # 参数字典
    kwargs['test_kwargs'] = dict()  # 回测参数字典
    kwargs['opts_kwargs'] = dict()  # 优化参数字典
    kwargs['log_kwargs'] = dict()  # 日志参数字典

    file_path_abs = dt_start = dt_end = dt_format = dt_dtformat = dt_tmformat = None
    if args.dtformat is not None:
        dt_format = args.dtformat
        dt_dtformat = dt_format[:dt_format.find('%d') + len('%d')]
        dt_tmformat = dt_format[dt_format.find('%H'):]
        # kwargs['dtformat'] = dt_format
        # kwargs['tmformat'] = dt_tmformat
    if args.fromdate is not None:
        dt_start = datetime.strptime(args.fromdate, dt_dtformat).date()
        # kwargs['fromdate'] = dt_start
    if args.todate is not None:
        dt_end = datetime.strptime(args.todate, dt_dtformat).date()
        # kwargs['todate'] = dt_end
    if args.data is not None:
        file_path = args.data
        myQuant_ROOT = os.getcwd()[:os.getcwd().find("bt_backtrader\\") + len("bt_backtrader\\")]  # 获取项目中相对根路径
        file_path_abs = os.path.join(myQuant_ROOT, file_path)  # 文件路径
        print(file_path_abs)
        # print("dt_format:", dt_format, "dt_start:", datetime.strftime(dt_start, "%Y-%m-%d"), "dt_end:", datetime.strftime(dt_end, "%Y-%m-%d"))
        if not os.path.exists(file_path_abs):
            raise Exception("数据源文件未找到！" + file_path_abs)
    if args.pwl is not None:
        kwargs['test_kwargs']['pwl'] = args.pwl
    if args.pw is not None:
        kwargs['test_kwargs']['pw'] = args.pw
    if args.pl is not None:
        kwargs['test_kwargs']['pl'] = args.pl
    if args.ojk is not None:
        kwargs['test_kwargs']['ojk'] = args.ojk
    if args.kpr is not None:
        kwargs['test_kwargs']['kpr'] = args.kpr

    # 加载数据
    df = pd.read_csv(filepath_or_buffer=file_path_abs,
                     # parse_dates={'datetime': ['date', 'time']},  # 日期和时间分开的情况
                     parse_dates=['datetime'],
                     index_col='datetime',
                     infer_datetime_format=True,
                     usecols=['datetime', 'open', 'close'],  # 要使用的数据列
                     )

    # df.sort_values(by=["datetime"], ascending=True, inplace=True)  # 按日期先后排序
    # df.sort_values(by=["date", "time"], ascending=True, inplace=True)  # 按日期时间列先后排序

    # df.index = pd.to_datetime(df.date + ' ' + df.time, format=dt_format)  # 方式1: 将日期列和时间合并后转换成日期类型,并设置成列索引
    # df.index = pd.to_datetime(df.date.astype(str) + ' ' + df.time.astype(str), format=dt_format)  # 方式2: 将日期列和时间合并后转换成日期类型,并设置成列索引
    # df.index = pd.to_datetime(df['date'] + ' ' + df['time'], format=dt_format)  # 方式3: 将日期列和时间合并后转换成日期类型,并设置成列索引
    # df.index = pd.to_datetime(df['date'], format=dt_dtformat) + pd.to_timedelta(df['time'])  # 方式4: 将日期列和时间合并后转换成日期类型,并设置成列索引
    # df.index = pd.to_datetime(df.pop('date')) + pd.to_timedelta(df.pop('time'))  # 方式5: 将日期列和时间合并后转换成日期类型,并设置成列索引
    # df.index = pd.to_datetime(df['date'].str.cat(df['time'], sep=' '), format=dt_format)  # 方式6: 将日期列和时间合并后转换成日期类型,并设置成列索引
    # 截取时间段内样本数据
    df = df[dt_start:dt_end]
    # df['openinterest'] = 0.00  # 增加一列openinterest
    # df = df[['open', 'high', 'low', 'close', 'volume']]  # 取出特定的列
    # df.rename(columns={"volume": "vol"}, inplace=True)  # 列名修改

    tframes = dict(
        minutes=bt.TimeFrame.Minutes,
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months)
    # data = bt.feeds.GenericCSVData(dataname=file_path, **kwargs)
    # 使用pandas数据源创建交易数据集
    data = (bt.feeds.PandasData(dataname=df, fromdate=dt_start, todate=dt_end))
    # 重采样到更大时间框架
    if args.timeframe and args.compression:
        data.resample(timeframe=tframes[args.timeframe], compression=args.compression)

    cerebro = bt.Cerebro(stdstats=False)

    cerebro.adddata(data)
    # 设置投资金额1000000
    cerebro.broker.setcash(G_INI_CASH)

    # # <editor-fold desc="折叠代码:交易手续费设置方式一">
    # cerebro.broker.setcommission(
    #     # 交易手续费，根据margin取值情况区分是百分比手续费还是固定手续费
    #     commission=0.00015,
    #     # commission=2.4,
    #     # 期货保证金，决定着交易费用的类型,只有在 stocklike=False 和 automargin=False时起作用
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
    #     # 如果automargin>0, 如果automargin*price确定保证金
    #     automargin=10 * 0.13,
    #     # 交易费用设置作用的数据集(也就是作用的标的)
    #     # 如果取值为None，则默认作用于所有数据集(也就是作用于所有assets)
    #     name=None
    # )
    # # </editor-fold>
    pass
    # <editor-fold desc="折叠代码:交易手续费设置方式二">
    comm = {
        'comm_sqrb': MyCommission(commtype=bt.CommInfoBase.COMM_PERC, commission=0.00015, margin_rate=0.13, mult=10.0),  # 螺纹钢合约信息
        'comm_zjif': MyCommission(commtype=bt.CommInfoBase.COMM_PERC, commission=0.00050, margin_rate=0.23, mult=300.0),  # 股指合约信息
        'comm_zqcf': MyCommission(commtype=bt.CommInfoBase.COMM_FIXED, commission=2.4, margin_rate=0.10, mult=10.0),  # 玉米合约信息
    }
    # 添加进 broker
    cerebro.broker.addcommissioninfo(comm[G_COMM], name=None)  # name 用于指定该交易费用函数适用的标的,未指定将适用所有标的
    # </editor-fold>

    file_name = ('{:}_{:}_{:}_{:}_{:}'
                 .format(G_FILE_PATH[:12], (str(G_DT_COMPRESSION) + (G_DT_TIMEFRAME[:1])), G_DT_START, G_DT_END,
                         (str(G_P_PARAM).replace('range', '')  # 替换路径中的range字符串
                          .translate(str.maketrans({' ': '', '\'': '', ':': '', }))),  # 将路径中的空格':字符替换成''
                         ))
    # 参数调优
    if args.opts:
        kwargs['opts_kwargs'] = G_P_PARAM  # 优化参数字典
        kwargs['opts_path'] = (file_name + '_opt.csv')  # 优化结果保存路径
        print('dt_start:', dt_start, 'dt_end:', dt_end)
        print('opts_kwargs:', kwargs['opts_kwargs'])
        # clock the start of the process
        tstart = time.perf_counter()
        # 为Cerebro引擎添加策略, 优化策略
        strats = cerebro.optstrategy(MyStrategy, **kwargs['opts_kwargs'])
        # 添加分析指标
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timeReturn', timeframe=bt.TimeFrame.Years)  # 此分析器通过查看时间范围的开始和结束来计算回报
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")  # 使用对数方法计算的总回报、平均回报、复合回报和年化回报
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyFolio')  # 添加PyFolio
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")  # 回撤
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")  # 夏普率
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="tradeAnalyzer")  # 提供有关平仓交易的统计信息（也保留未平仓交易的数量）
        cerebro.addanalyzer(My_TradeAnalyzer, _name="my_tradeAnalyzer")  # 自定义平仓交易的统计信息
        # Run over everything
        results_opt = cerebro.run(
            maxcpus=args.maxcpus,
            optdatas=not args.no_optdatas,  # optdatas（默认值：True)如果和优化（以及系统可以和使用），数据预加载将只在主进程中完成一次，以节省时间和资源。
            optreturn=not args.no_optreturn,  # optreturn（默认值：True)如果优化结果不是完整的对象（以及所有数据、指标、观察器等），而是具有以下属性的对象 在大多数情况下，只有分析器和哪些参数是评估策略性能所需的东西。如果需要对（例如）指标的生成值进行详细分析，请将其关闭
            # optreturn=False,
            # stdstats=False,
        )
        # clock the end of the process
        tend = time.perf_counter()
        # print out the result_one
        print('Time used:', str(tend - tstart))
        print("--------------- 分析结果 -----------------")

        # 每个策略实例的结果以列表的形式保存在列表中。优化运行模式下，返回值是列表的列表,内列表只含一个元素，即策略实例
        res_list = [[]]
        res_timereturn_title = []  # 列标题

        timeReturn = results_opt[0][0].analyzers.timeReturn.get_analysis()  # timeReturn 分析引用
        for k, v in timeReturn.items():
            res_timereturn_title.append('{:%Y-%m}'.format(k))
        res_df = pd.DataFrame()  # 新建一个空的pandas列表,内容由字典填充

        for i, x in enumerate(results_opt):
            trade = x[0].analyzers.tradeAnalyzer.get_analysis()  # 交易分析引用
            my_trade = x[0].analyzers.my_tradeAnalyzer.get_analysis()  # 交易分析引用
            returns = x[0].analyzers.returns.get_analysis()  # 回报分析引用
            pyFolio = x[0].analyzers.pyFolio.get_analysis()  # pyFolio分析引用
            drawdown = x[0].analyzers.drawdown.get_analysis()  # 回撤分析引用
            sharpe = x[0].analyzers.sharpe.get_analysis()  # sharpe分析引用
            timeReturn = x[0].analyzers.timeReturn.get_analysis()  # timeReturn 分析引用

            if trade['total']['total'] == 0:
                continue  # 忽略交易次数为0 的数据

            returns_rort_ = returns['rtot'] * 100  # 总复合回报
            pyFolio_returns_ = sum(pyFolio['returns'].values()) * 100  # pyFolio总复合回报
            returns_rnorm100_ = returns['rnorm100'] * 100  # 年化归一化回报
            trade_won_ = (trade['won']['total']) if 'won' in trade else 0  # 总盈利次数
            trade_lost_ = (trade['lost']['total']) if 'lost' in trade else 0  # 总亏损次数
            trade_total_ = trade['total']['total']  # 交易次数
            trade_win_rate = (trade_won_ / trade_total_) * 100  # 胜率
            drawdown_ = drawdown['max']['drawdown'] if 'max' in drawdown else 0  # 最大回撤
            sharpe_ = sharpe['sharperatio'] if 'sharperatio' in sharpe else 0  # 夏普率
            trade_pnl_total_ = (trade['pnl']['gross']['total']) if 'pnl' in trade else 0  # 总盈亏
            trade_pnl_net_ = (trade['pnl']['net']['total']) if 'pnl' in trade else 0  # 总盈亏-手续费
            trade_pnl_comm_ = abs(trade_pnl_total_ - trade_pnl_net_)  # 手续费
            trade_comm_net_p = ((trade_pnl_comm_ / trade_pnl_net_) * 100) if trade_pnl_net_ != 0 else 0  # 手续费占比净盈亏百分比

            row = dict()
            for pk, pv in G_P_PARAM.items():  # 遍历参数列表,将需要优化的参数名和值添加到字典里
                if type(pv) == list or type(pv) == range:
                    row[pk] = x[0].p._get(pk)
            row.update({
                'pwl': x[0].p.pwl,  # 参数
                'pw': x[0].p.pw,  # 参数
                'pl': x[0].p.pl,  # 参数
                'ojk': x[0].p.ojk,  # 参数
                'total': '{:0>4d}'.format(trade_total_),  # 交易次数
                'sharpe': sharpe_,  # 夏普率
                'rtot%': returns_rort_,  # 总复合回报
                'py_rt%': pyFolio_returns_,  # pyFolio总复合回报
                'won%': trade_win_rate,  # 胜率
                'rnorm%': returns_rnorm100_,  # 年化归一化回报
                'maxDD%': round(drawdown_, 3),  # 最大回撤
                'comm%': round(trade_comm_net_p, 3),  # 手续费占比净盈亏百分比
                'pnl_net': '{:8.2f}'.format(trade_pnl_net_),  # 总盈亏余额含手续费
            })
            for k, v in timeReturn.items():  # 把timeReturn统计的月度或年度复合回报添加在后面 # 月度或年度复合回报,由参数timeframe=bt.TimeFrame.Months控制
                row['{:%Y-%m}'.format(k)] = v
            res_df = res_df.append(row, ignore_index=True)
        res_df.loc[:, :'total'] = res_df.loc[:, :'total'].astype(int)  # 转换指定total列前的数据类型
        if bool(res_df.empty):
            print('回测数据不存在')
        if not ('pw' in G_P_PARAM or 'pl' in G_P_PARAM):
            # 删除未优化的参数列
            res_df = res_df.drop(labels=['pw', 'pl'], axis=1)
        if not ('ojk' in G_P_PARAM):
            res_df = res_df.drop(labels=['ojk'], axis=1)
        if not ('pwl' in G_P_PARAM):
            res_df = res_df.drop(labels=['pwl'], axis=1)

        res_df = res_df.dropna(how='any', axis=0)  # 删除所有带NaN的行
        # res_df[['pw', 'pl', 'ojk', 'total']] = res_df[['pw', 'pl', 'ojk', 'total']].apply(pd.to_numeric, downcast='signed', axis=1)  # 转换指定列数据类型为整形
        res_df[['rtot%', 'pnl_net']] = res_df[['rtot%', 'pnl_net']].apply(pd.to_numeric, errors='ignore', axis=1)

        res_df.sort_values(by=['pnl_net', 'rtot%'], ascending=False, inplace=True)  # 按累计盈亏和总复合回报排序
        # res_df.reset_index(drop=True, inplace=True)  # 重设索引id,删除旧索引,替换新索引
        res_df.index.name = 'id'  # 设置索引名称
        pd.set_option('precision', 3)  # 显示小数点后的位数
        pd.set_option('display.min_rows', 300)  # 确定显示的部分有多少行
        pd.set_option('display.max_rows', 300)  # 确定显示的部分有多少行
        pd.set_option('display.max_columns', 20)  # 确定显示的部分有多少列
        pd.set_option('display.float_format', '{:,.2f}'.format)  # 逗号格式化大值数字,设置数据精度
        pd.set_option('expand_frame_repr', False)  # True就是可以换行显示。设置成False的时候不允许换行
        pd.set_option('display.width', 180)  # 设置打印宽度(**重要**)

        res_df[res_df.columns[:5]].info()  # 显示前几列的数据类型
        if not res_df.empty:
            G_RESULT_ONE = result_one = results_opt[res_df.index[0]]  # 返回第一个参数测试结果
        opts_path = kwargs['opts_path']
        print(opts_path)  # 打印文件路径
        print(res_df.loc[:, :'pnl_net'])  # 显示 开始列到'pnl_net'列的 参数优化结果
        res_df.to_csv(opts_path, sep='\t', float_format='%.2f')  # 保存分析数据到文件
        print("--------------- 优化结束 -----------------")
    # 回测分析
    else:
        # test_kwargs = kwargs['test_kwargs']
        test_kwargs = G_P_PARAM  # 回测参数
        log_logger = None
        if G_P_LOG_PRINT or G_P_LOG_FILE:
            log_logger = logger_config(log_path=(file_name + '_log.txt'), log_name='交易日志')
        # 回测日志参数
        log_kwargs = dict(
            log_logger=log_logger,
            log_print=G_P_LOG_PRINT,  # 是否打印日志到控制台
            log_save=G_P_LOG_FILE,  # 是否保存日志到文件
        )
        print('dt_start:', dt_start, 'dt_end:', dt_end)
        print('test_kwargs:', test_kwargs)  # 回测参数
        print('log_kwargs:', log_kwargs)  # 日志参数
        # 添加观测器,绘制时显示
        cerebro.addobserver(bt.observers.Broker)
        cerebro.addobserver(bt.observers.Trades)
        cerebro.addobserver(bt.observers.BuySell)
        # cerebro.addobserver(bt.observers.TimeReturn)
        cerebro.addobserver(bt.observers.DrawDown)
        # 添加分析指标
        cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualReturn')  # 返回年初至年末的年度收益率
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawDown')  # 计算最大回撤相关指标
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns', tann=252)  # 计算年化收益：日度收益
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyFolio')  # 添加PyFolio
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpeRatio', timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0)  # 计算年化夏普比率：日度收益
        cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='sharpeRatio_A')
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timeReturn', )  # 添加收益率时序
        cerebro.addanalyzer(My_TradeAnalyzer, _name="my_tradeAnalyzer")  # 自定义平仓交易的统计信息

        # 添加策略和参数
        cerebro.addstrategy(MyStrategy, log_kwargs=log_kwargs, **test_kwargs)

        # 引擎运行前打印期出资金
        print('组合期初资金: %s' % format(cerebro.broker.getvalue(), ',.2f'))
        # 启动回测
        result_one = cerebro.run()
        # 引擎运行后打期末资金
        print('组合期末资金: %s' % format(cerebro.broker.getvalue(), ',.2f'))
        # 提取结果
        print("\n--------------- 累计收益率 -----------------")
        returns = result_one[0].analyzers.returns.get_analysis()
        pyFolio = result_one[0].analyzers.pyFolio.get_analysis()
        print(" Cumulative Return%: {:.2f}%".format(returns['rtot'] * 100))
        print(" pyFolio Cumulative Return%: {:,.2f}".format(sum(pyFolio['returns'].values()) * 100))
        print("\n--------------- 年度收益率 -----------------")
        annualReturn = result_one[0].analyzers.annualReturn.get_analysis()
        # print(' 收益率k,v', get_analysis.items())
        for k, v in annualReturn.items():
            print((" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v), end='')
        print("\n--------------- 最大回撤 -----------------")
        drawDown = result_one[0].analyzers.drawDown.get_analysis()
        for k, v in drawDown.items():
            if not isinstance(v, dict):
                t = (" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v)
                print(t, end='')
            else:
                for kk, vv in v.items():
                    t = (" [{:},{:.2f}]" if isinstance(vv, float) else " [{:},{:}]").format(kk, vv)
                    print(t, end='')
        print("\n--------------- 年化收益：日度收益 -----------------")
        an_returns = result_one[0].analyzers.returns.get_analysis()
        for k, v in an_returns.items():
            print((" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v), end='')
        print("\n--------------- 年化夏普比率：日度收益 -----------------")
        sharpeRatio = (result_one[0].analyzers.sharpeRatio.get_analysis())
        for k, v in sharpeRatio.items():
            print((" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v), end='')
        print("\n--------------- SharpeRatio_A -----------------")
        sharpeRatio_A = result_one[0].analyzers.sharpeRatio_A.get_analysis()
        for k, v in sharpeRatio_A.items():
            print((" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v), end='')
        print("\n--------------- test end -----------------")
        # 在记录日志之后移除句柄
        if G_P_LOG_PRINT or G_P_LOG_FILE:
            log_logger.streamHandler.close()
            log_logger.fileHandler.close()
            logging.shutdown()  # 关闭日志系统
    # 绘图
    if args.plot and not args.opts:
        pkwargs = dict(style='bar')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(volume=False, **pkwargs)  # 绘图BT观察器结果

        # 结合pyfolio工具 计算并绘制收益评价指标
        import pyfolio as pf
        # 绘制图形
        import matplotlib.pyplot as plt
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        import matplotlib.ticker as ticker  # 导入设置坐标轴的模块
        # plt.style.use('seaborn')
        plt.style.use('dark_background')

        # 提取收益序列
        pnl = pd.Series(result_one[0].analyzers.timeReturn.get_analysis())
        # 计算累计收益
        cumulative = (pnl + 1).cumprod()
        # 计算回撤序列
        max_return = cumulative.cummax()
        drawdown = (cumulative - max_return) / max_return
        # 按年统计收益指标
        perf_stats_year = pnl.groupby(pnl.index.to_period('y')).apply(lambda data: pf.timeseries.perf_stats(data)).unstack()
        # 统计所有时间段的收益指标
        perf_stats_all = pf.timeseries.perf_stats(pnl).to_frame(name='all')
        perf_stats = pd.concat([perf_stats_year, perf_stats_all.T], axis=0)
        perf_stats_ = round(perf_stats, 4).reset_index()

        fig, (ax0, ax1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 4]}, figsize=(24, 16))
        cols_names = ['date', 'Annual\nreturn', 'Cumulative\nreturns', 'Annual\n volatility',
                      'Sharpe\nratio', 'Calmar\nratio', 'Stability', 'Max\ndrawdown',
                      'Omega\nratio', 'Sortino\nratio', 'Skew', 'Kurtosis', 'Tail\nratio',
                      'Daily value\nat risk']
        # 绘制表格
        ax0.set_axis_off()  # 除去坐标轴
        table = ax0.table(cellText=perf_stats_.values,
                          bbox=(0, 0, 1, 1),  # 设置表格位置， (x0, y0, width, height)
                          rowLoc='left',  # 行标题居中
                          cellLoc='left',
                          colLabels=cols_names,  # 设置列标题
                          colLoc='left',  # 列标题居中
                          edges='open'  # 不显示表格边框
                          )
        table.set_fontsize(13)

        # 绘制累计收益曲线
        ax2 = ax1.twinx()
        ax1.yaxis.set_ticks_position('right')  # 将回撤曲线的 y 轴移至右侧
        ax2.yaxis.set_ticks_position('left')  # 将累计收益曲线的 y 轴移至左侧
        # 绘制回撤曲线
        drawdown.plot.area(ax=ax1, label='drawdown (right)', rot=0, alpha=0.3, fontsize=13, grid=False)
        # 绘制累计收益曲线
        cumulative.plot(ax=ax2, color='#F1C40F', lw=2.0, label='cumret (left)', rot=0, fontsize=13, grid=False)
        # 不然 x 轴留有空白
        ax2.set_xbound(lower=cumulative.index.min(), upper=cumulative.index.max())
        # 主轴定位器：每 5 个月显示一个日期：根据具体天数来做排版
        ax2.xaxis.set_major_locator(ticker.MultipleLocator(120))
        # 同时绘制双轴的图例
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()

        plt.legend(h1 + h2, l1 + l2, fontsize=12, loc='upper left', ncol=1)
        fig.tight_layout()  # 规整排版
        plt.show()
        # 结合pyfolio工具 计算并绘制收益评价指标
    # 回测分析保存到文件
    if args.quantstats and not args.opts:
        # 使用quantstats 分析工具并保存到HTML文件
        import quantstats
        portfolio_stats = result_one[0].analyzers.getbyname('pyFolio')
        returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
        returns.index = returns.index.tz_convert(None)
        param_one = dict()
        for pk, pv in G_P_PARAM.items():  # 遍历参数列表,将优化的参数名和值添加到字典里
            param_one[pk] = result_one[0].p._get(pk)
        import quantstats
        # 将分析指标保存到HTML文件
        title_report = ('{:}-{:} st={:%Y-%m-%d} end={:%Y-%m-%d} pam={:} dt={:%H.%M.%S}'  # 优化结果网页标题
            .format(
            (G_FILE_PATH.split('\\')[1].split('-')[0]),  # 合约名称
            str(G_DT_COMPRESSION) + (G_DT_TIMEFRAME[:1]),  # K线周期
            datetime.fromisoformat(G_DT_START), datetime.fromisoformat(G_DT_END),  # 开始结束时间
            (str(param_one).replace('range', '')  # 替换参数字典中的字符串
             .translate(str.maketrans({' ': '', '\'': '', ':': ''}))),  # 替换参数字典中的字符
            datetime.now(),
        ))
        quantstats.reports.html(returns, output='stats.html', title=title_report)
        print("quantstats 测试分析结果已保存至目录所在文件 quantstats-tearsheet.html")
        # 使用quantstats 分析工具并保存到HTML文件
        pass


def logger_config(log_path, log_name):
    """
    配置log
    :param log_path: 输出log路径
    :param log_name: 记录中name，可随意
    :return:
    """
    '''
    logger是日志对象，handler是流处理器，console是控制台输出（没有console也可以，将不会在控制台输出，会在日志文件中输出）
    '''
    # 获取logger对象,取名
    logger = logging.getLogger(log_name)
    # 输出DEBUG及以上级别的信息，针对所有输出的第一层过滤
    logger.setLevel(level=logging.DEBUG)
    # 获取文件日志句柄并设置日志级别，第二层过滤
    if log_path:
        logger.fileHandler = logging.FileHandler(log_path, encoding='UTF-8')
        logger.fileHandler.setLevel(logging.INFO)  # 设置文件日志输出级别 设置 INFO 时debug信息将不显示
        # 生成并设置文件日志格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger.fileHandler.setFormatter(formatter)
        logger.addHandler(logger.fileHandler)  # 为logger对象添加句柄
    # console相当于控制台输出，handler文件输出。获取流句柄并设置日志级别，第二层过滤
    logger.streamHandler = logging.StreamHandler(stream=sys.stdout)
    # logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    logger.streamHandler.setLevel(logging.INFO)  # 设置控制台显示级别 日志级别： debug < info < warning < error < critical
    logger.addHandler(logger.streamHandler)  # 为logger对象添加句柄
    return logger


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


class Target(Enum):
    """枚举开仓类型"""
    TARGET_SIZE = "数量"  # 成交量
    TARGET_VALUE = "金额"  # 目标金额
    TARGET_PERCENT = "百分比"  # 百分比


# 创建策略继承bt.Strategy
class MyStrategy(bt.Strategy):

    def log(self, txt, dt=None, printlog=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.datetime(0)
        # 时间断点调试,调试条件 self.datas[0].dtdt.dtdt(0) >= bt.dtdt.dtdt.strptime('2018-01-23 14:05:00','%Y-%m-%d %H:%M:%S')
        # print('%s, %s' % (dt.isoformat(), txt))
        txt = ('%s, %s' % (dt.strftime('%a %Y-%m-%d %H:%M:%S'), txt))
        # 使用日志系统输出
        if self.p.log_kwargs and self.log_logger:
            if self.p.log_kwargs['log_save']:
                if hasattr(self.log_logger, 'fileHandler'):
                    self.log_logger.fileHandler.setLevel(logging.DEBUG)  # 将debug日志信息输出到文件
            if self.p.log_kwargs['log_print'] or printlog:
                if hasattr(self.log_logger, 'streamHandler'):
                    self.log_logger.streamHandler.setLevel(logging.DEBUG)  # 将debug日志信息输出到控制台
            self.log_logger.debug(txt)  # 输出debug信息到日志系统
        # 使用print打印日志
        elif self.p.log_print or printlog:
            print('print:', txt)

    params = dict(
        pwl=10,  # 盈亏千分比
        pw=0,  # 盈利千分比
        pl=0,  # 亏损千分比
        ok=0,  # 入场开仓单位 按(数量,金额,百分比)下单
        po=0,  # 入场开仓加减幅度百分比
        pp=0,  # 盈亏加减幅度百分比
        pmax=0,  # 最大开仓单位
        ojk=1,  # 订单间隔bar周期数
        llp=0,  # 最大回撤千分比
        kpr=[],  # 加仓方向的关价格点位 kpr=0无限制,向上穿越 kpr 时只有多头加仓,向下穿越 kpr 时只有空头加仓
        valid=None,  # 订单生效时间
        log_print=False,  # 是否打印日志到控制台
        log_save=False,  # 是否保存日志到文件
        log_kwargs=dict(),  # 日志参数字典
        tar=Target.TARGET_PERCENT.value,  # T_PERCENT 按目标百分比下单 T_SIZE,  # 按目标数量下单 T_VALUE,  # 按目标金额下单
    )

    def __init__(self):
        # super().__init__(*args, **kwargs)
        if self.p.log_kwargs:
            self.p.log_print = self.p.log_kwargs['log_print']
            self.p.log_save = self.p.log_kwargs['log_save']
            self.log_logger = self.p.log_kwargs['log_logger']  # 获取logger对象
        else:
            self.log_logger = None
        # 如果未赋值,则使用默认参数
        if self.p.tar == TargetType.T_SIZE.value:
            self.p.ok = self.p.ok if self.p.ok else 1
            self.p.pmax = self.p.pmax if self.p.pmax else 100
        elif self.p.tar == TargetType.T_VALUE.value:
            self.p.ok = self.p.ok if self.p.ok else self.broker.getcash() * 0.10
            self.p.pmax = self.p.pmax if self.p.pmax else self.broker.getcash()
        elif self.p.tar == TargetType.T_PERCENT.value:
            self.p.ok = self.p.ok if self.p.ok else 10.0
            self.p.pmax = self.p.pmax if self.p.pmax else 100.0
        self.p_pwl = self.p.pwl / 1000  # 盈亏千分比
        self.p_pw = (self.p.pw if self.p.pw else self.p.pwl) / 1000  # 盈利千分比
        self.p_pl = (self.p.pl if self.p.pl else self.p.pwl) / 1000  # 亏损千分比
        self.p_ok = self.p.ok  # 开仓单位
        self.p_pok_min = self.p.ok  # 最小开仓单位
        self.p_pok_max = self.p.pmax  # 最大开仓单位
        self.p_po = self.p.po / 100  # 入场开仓加减幅度百分比
        self.p_pp = self.p.pp / 100  # 盈亏加减幅度百分比
        self.mpwa = self.p_pw  # 加仓盈利千分比
        self.mpla = self.p_pl  # 加仓亏损千分比
        self.entry_mpok = self.p_ok  # 入场时的开仓单位
        self.entry_order = dict()  # 入场订单
        self.order_datetime: datetime = None  # 订单发生时间
        self.entry_price_begin = 0.0  # 初始入场价格
        self.entry_price = 0.0  # 入场价格
        self.entry_price_ref1 = 0.0  # 上一次入场价格
        self.exit_price = 0.0  # 离场价格
        self.order_this_bar = 0  # 该周期是否有交易 0没有,1有
        self.bar_executed = 0  # 记录当前交易的bar序列
        self.turtleunits = 0  # 加仓次数
        self.numlosst = 0  # 统计连续亏损次数
        self.ppunit = 1  # 交易手数比率
        self.ppos_profit_ref1 = 0.0  # 上一笔交易盈亏幅度
        self.position_flag = 0  # 仓位状态 0表示没有仓位，1表示持有多头， -1表示持有空头
        self.radd = 0  # 盈利加仓价格
        self.lout = 0  # 亏损退出价格
        self.sig_ref1 = 0  # 记录上一次入场信号 1多头,-1空头,0无
        self.sig_long = 0  # 多头条件
        self.sig_short = 0  # 空头条件
        self.sig_longa1 = 0  # 多头加仓条件
        self.sig_shorta1 = 0  # 空头加仓条件
        self.sig_long_dec = 0  # 多头减仓条件
        self.sig_short_dec = 0  # 空头减仓条件
        self.sig_longx1 = 0  # 多头离场条件
        self.sig_shortx1 = 0  # 空头离场条件
        self.sig_long_keyPoint = False  # 存在向上穿越关键价格点
        self.sig_short_keyPoint = False  # 存在向下穿越关键价格点
        self.mbstop = 0  # 是否触发回撤止损
        self.pl_sum = 0  # 累计连续亏损百分比
        self.dtopen_month = 0.0  # 记录每月开盘价
        self.initial_amount = 0.0  # 初始金额

        # 建立对于DataFeed的Open/Close价格的引用参数
        self.dtdt: datetime = self.datas[0].datetime  # 日期时间
        self.dtdate = self.datas[0].datetime.date  # 日期
        self.dtopen = self.datas[0].open
        self.dtclose = self.datas[0].close
        # self.dthigh = self.datas[0].high
        # self.dtlow = self.datas[0].low

        # 跟踪挂单
        self.myorder = None

    def start(self):
        """在回测开始之前调用,对应第0根bar"""
        # 回测开始之前的有关处理逻辑可以写在这里
        # 默认调用空的 start() 函数，用于启动回测
        self.myorder = None  # 哨兵避免挂单操作
        self.dtopen_month = self.dtopen[0]
        self.initial_amount = self.broker.getcash()

    def notify_trade(self, trade):
        """每当有交易订单状态发生改变时通知信息"""
        if not trade.isclosed:
            return
        t = 'notify_trade:'
        t += ',盈亏, {:.2f},comm {:.2f}, NET {:.2f}'.format(
            trade.pnl,  # 盈亏
            (trade.pnl - trade.pnlcomm),  # 手续费
            trade.pnlcomm)  # 盈亏含手续费
        t += ',add:{:.2f}'.format(self.radd)
        t += ',lout:{:.2f}'.format(self.lout)
        t += ',open_m:{:}'.format(self.dtopen_month)
        t += ',总资产:{:,.2f}'.format(self.broker.getvalue())
        # t += ',回撤:{:.2f}'.format(self.stats.drawdown.drawdown[0])
        # t += ',收益率:{:.3f}'.format(self.stats.timereturn.line[0])
        t += ',开仓比:{:.0f}%'.format(self.p_ok)

        self.log(t, dt=self.dtdt.datetime(0))

    def notify_order(self, order):
        """每当有交易订单生成时通知信息"""
        if order.status in [order.Submitted, order.Accepted]:
            # broker 提交/接受了，买/卖订单则什么都不做
            # self.log('order.OrdTypes:{:},size:{:}'.format(order.OrdTypes[order.ordtype], order.size))
            return
        t = 'notify_order:'
        # t += ',month:{:}'.format(self.dtdate(0).month)
        # t += ',month:{:}'.format(self.dtdate(-1).month)
        # 检查一个订单是否完成
        # 注意: 当资金不足时，broker会拒绝订单
        if order.status in [order.Completed]:
            if order.isbuy():
                t += ',已买入'
            elif order.issell():
                t += ',已卖出'
            # 记录当前交易数量
            t += (',成交:{:d},持仓:{:d},Price:{:.2f},Cost:{:.2f},Comm:{:.2f}'.format(
                order.executed.size,  # 成交量 开仓数量
                self.position.size,  # 持仓
                order.executed.price,  # 成交价
                order.executed.value,  # 占成交额 用保证金
                order.executed.comm))  # 佣金 手续费
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order.isbuy():
                t += ',买入单'
            elif order.issell():
                t += ',卖出单'
            t += ',订单取消/保证金不足/拒绝'
            t += ',持仓:{:d}'.format(self.position.size)
            t += ',Price:{:.2f}'.format(self.dtclose[0])

        t += ',add:{:.2f}'.format(self.radd)
        t += ',lout:{:.2f}'.format(self.lout)
        t += ',open_m:{:}'.format(self.dtopen_month)
        t += ',m_rate:{:}'.format(self.broker.getcommissioninfo(data=self.data).p.margin_rate)  # 获取保证比率
        t += ',margin:{:.2f}'.format(self.broker.getcommissioninfo(data=self.data).get_margin(self.dtclose[0]))  # 最低开仓保证金
        t += ',可用资金:{:.2f}'.format(self.broker.getcash())
        t += ',持仓市值:{:.2f}'.format(self.broker.getvalue(datas=[self.data]))
        t += ',总资产:{:,.2f}'.format(self.broker.getvalue())
        t += ',开仓比:{:.0f}%'.format(self.p_ok)

        self.log(t, dt=self.dtdt.datetime(0))
        if not order.alive():
            self.myorder = None  # 表示没有订单待处理

    def order_target(self, size=None, data=None):
        """订单开仓头寸管理"""
        size = size if size else self.p_ok
        dt = self.data.datetime[0]
        # 时间断点调试,调试条件 self.datas[0].datetime.datetime(0) >= bt.datetime.datetime.strptime('2012-10-18 13:30:00','%Y-%m-%d %H:%M:%S')
        if isinstance(dt, float):
            dt = bt.num2date(dt)

        # data = data if data else self.data
        # if isinstance(data, str):
        #     data = self.getdatabyname(data)
        # elif data is None:
        #     data = self.databyname(data)
        # # print('%04d - %s - Order Target Size: %02d' % (len(self), dt.isoformat(), size))

        poskkcash = 0.0  # 开仓单位
        posmincash = 0.0  # 最小开仓单位
        posmaxcash = 0.0  # 最大开仓单位
        comminfo = self.broker.getcommissioninfo(self.data)
        margin = comminfo.get_margin(self.dtclose[0])  # 最低开仓保证金
        margin_cash = self.broker.getvalue(datas=[self.data])  # 持仓头寸占用资金
        # margin = bt.Order.comminfo.get_margin(self.dtclose[0])  # 最低开仓保证金
        get_cash = abs(self.broker.getcash())  # 可用资金
        get_cash_value = abs(self.broker.getvalue())  # 账户总资金
        sign = np.sign(self.p_ok)  # 取正负符号
        self.p_ok = abs(self.p_ok)
        open_profit = sign * self.position.size * (self.position.price - self.dtclose[0])  # 浮动盈亏
        total_return = (get_cash_value - self.initial_amount) / self.initial_amount  # 总回报率

        # 按成交量下单
        if self.p.tar == TargetType.T_SIZE.value:
            # poskkcash = margin * abs(size)  # 开仓金额
            posmincash = min(margin * 1.1, get_cash)  # 最小开仓金额
            posmaxcash = min(max(margin * 1.1, (margin * self.p_pok_max)), get_cash)  # 最大开仓金额
            percent = abs(self.p_ok * margin / get_cash_value)  # 目标持仓比率
            poskkcash = percent * (get_cash - open_profit - self.initial_amount) if total_return > 100 else percent * (get_cash - open_profit)  # 总盈利>初始金额时,使用盈利金额交易

            # 限定使用资金的范围
            poskkcash = abs(  # sign 为开仓方向
                get_cash if (posmincash > get_cash)  # 最小开仓金额>可用金额时,使用可用金额
                else (  # 最小开仓金额<可用金额时
                    (poskkcash * (1.01 + abs(self.p_po))) if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,适当增加开仓比率
                    # posmincash if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,使用最小开仓金额
                    else (posmaxcash if (abs(poskkcash) > posmaxcash)  # 开仓金额>最大开仓金额时,使用最大开仓金额
                          else poskkcash)))
            target = int(sign * round((poskkcash + margin_cash) // margin))
            self.myorder = self.order_target_size(target=target)
            self.p_ok = target

        # 按目标金额下单
        elif self.p.tar == TargetType.T_VALUE.value:
            # self.mpok为目标持仓金额, > margin_cash时 为加仓, < margin_cash时 为减仓
            posmincash = min(margin * 1.1, get_cash)  # 最小开仓金额
            posmaxcash = min(max(margin * 1.1, (1 * self.p_pok_max)), get_cash)  # 最大开仓金额
            percent = abs(self.p_ok / get_cash_value)  # 目标持仓比率
            poskkcash = percent * (get_cash - open_profit - self.initial_amount) if total_return > 100 else percent * (get_cash - open_profit)  # 总盈利>初始金额时,使用盈利金额交易

            # 限定使用资金的范围
            poskkcash = abs(  # sign 为开仓方向
                get_cash if (posmincash > get_cash)  # 最小开仓金额>可用金额时,使用可用金额
                else (  # 最小开仓金额<可用金额时
                    (poskkcash * (1.01 + abs(self.p_po))) if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,适当增加开仓比率
                    # posmincash if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,使用最小开仓金额
                    else (posmaxcash if (abs(poskkcash) > posmaxcash)  # 开仓金额>最大开仓金额时,使用最大开仓金额
                          else poskkcash)))
            value = sign * (poskkcash + margin_cash)
            self.myorder = self.order_target_value(target=value)
            self.p_ok = poskkcash

        # 按目标百分比下单
        elif self.p.tar == TargetType.T_PERCENT.value:
            posmincash = min(margin * 1.1, get_cash)  # 最小开仓金额
            posmaxcash = min(max(margin * 1.1, (get_cash * self.p_pok_max)), get_cash)  # 最大开仓金额
            # percent = (margin_cash / get_cash)  # 持仓头寸占可用资金比率
            # percent = (margin_cash / get_cash_value)  # 持仓头寸占总资金比率
            percent = abs(self.p_ok / 100)  # 目标持仓比率

            # poskkcash = percent * (get_cash - open_profit)  # (可用资金-浮动盈亏)金额百分比交易
            poskkcash = percent * (get_cash - open_profit - self.initial_amount) if total_return > 100 else percent * (get_cash - open_profit)  # 总盈利>初始金额时,使用盈利金额交易
            # poskkcash = percent * (get_cash_value - open_profit)  # 帐户总资金百分比交易

            # 限定使用资金的范围
            poskkcash = abs(  # sign 为开仓方向
                get_cash if (posmincash > get_cash)  # 最小开仓金额>可用金额时,使用可用金额
                else (  # 最小开仓金额<可用金额时
                    (poskkcash * (1.01 + abs(self.p_po))) if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,适当增加开仓比率
                    # posmincash if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,使用最小开仓金额
                    else (posmaxcash if (abs(poskkcash) > posmaxcash)  # 开仓金额>最大开仓金额时,使用最大开仓金额
                          else poskkcash)))

            percent = sign * abs((poskkcash + margin_cash) / get_cash_value)  # 计算占用账户总资金的百分比
            self.myorder = self.order_target_percent(target=percent)
            self.p_ok = percent * 100

        return self.myorder

    def next(self):
        """每当有新的k线周期生成时通知信息"""
        # self.log('Close, %.2f' % self.dtclose[0], dt=bt.num2date(self.dtdt[0]))  # 打印当前收盘价 bt.num2date(self.dtdt[0]) 日期数值转换
        # self.log('dt, {:}'.format((self.dtdt.datetime(0) - self.dtdt.datetime(-1)).total_seconds() / 60))  # 计算与一个时间序列的间隔分钟数
        # if (round(self.dtdate(0).month // 3) % 4) != (round(self.dtdate(-1).month // 3) % 4):  # 记录每个季度open价
        if self.order_datetime:  # 判断订单时间是否小于间隔周期
            dt1 = (self.dtdt.datetime(0) - self.order_datetime).total_seconds() / 60  # 订单时间到当前bar的间隔分钟数
            dt2 = (self.dtdt.datetime(0) - self.dtdt.datetime(-1)).total_seconds() / 60  # 与前一个bar的间隔分钟数
            dt3 = dt1 // dt2  # 订单间隔周期数
            dt4 = dt3 % dt2  # 间隔周期数取模(0-dt2)
            # print(self.dtdt.datetime(0).strftime("%Y-%m-%d %H:%M:%S"), self.order_datetime.strftime("%Y-%m-%d %H:%M:%S"), 'C:', self.dtclose[0], 'dt1:', dt1, 'dt2:', dt2, 'dt3:', dt3, 'dt4:', dt4)
            if dt3 < self.p.ojk:
                return
        # 如果有订单正在挂起，不操作
        if self.myorder:
            return
        if (round(self.dtdt.date(0).month)) != (round(self.dtdt.date(-1).month)):  # 记录每个月open价
            self.dtopen_month = self.dtopen[0]
        self.order_this_bar = 0  # 标记该周期的交易状态
        assets = self.broker.getvalue()  # 当前总资产

        # 多头入场条件
        self.sig_long = (
                not self.position  # 空仓时
                and self.position.size == 0  # 持仓为0
                and self.dtclose[0] > self.dtopen[0]
                and assets > 0  # 当前总资产>0
        )
        # 空头入场条件
        self.sig_short = (
                not self.position  # 空仓时
                and self.position.size == 0  # 持仓为0
                and self.dtclose[0] < self.dtopen[0]
                and assets > 0  # 当前总资产>0
        )
        if self.p.kpr:
            for kp in self.p.kpr:
                if self.dtclose[-1] >= kp and (self.dtclose[-2] < kp):  # 向上穿越关键点后加多仓
                    self.sig_long_keyPoint = True
                    self.sig_short_keyPoint = False
                if self.dtclose[-1] <= kp and (self.dtclose[-2] > kp):  # 向下穿越关键点后加空仓
                    self.sig_long_keyPoint = False
                    self.sig_short_keyPoint = True
        # 多头加仓条件
        self.sig_longa1 = (self.position_flag == 1
                           and (self.dtclose[0] > self.dtopen_month)
                           # and (self.dthigh[0] > self.dtlow[0])
                           and (self.dtclose[0] >= self.radd)
                           and self.order_this_bar == 0)
        # 多头减仓条件
        self.sig_long_dec = 1 and self.sig_long_keyPoint
        # 空头加仓条件
        self.sig_shorta1 = (self.position_flag == -1
                            and (self.dtclose[0] < self.dtopen_month)
                            # and (self.dthigh[0] > self.dtlow[0])
                            and (self.dtclose[0] <= self.radd)
                            and self.order_this_bar == 0)
        # 空头减仓条件
        self.sig_short_dec = 1 and self.sig_short_keyPoint
        # 多头离场条件 添加OPEN价离场条件
        self.sig_longx1 = (self.position_flag == 1
                           # and self.dthigh[0] > self.dtlow[0]
                           and (self.dtclose[0] <= self.lout or self.dtopen[0] <= self.lout))
        # 空头离场条件 添加OPEN价离场条件
        self.sig_shortx1 = (self.position_flag == -1
                            # and self.dthigh[0] > self.dtlow[0]
                            and (self.dtclose[0] >= self.lout or self.dtopen[0] >= self.lout))

        t_enter = t_add = t_exit = t_dec = 'next:'

        # 当有信号发生时,更新订单时间
        if (self.sig_long or self.sig_short
                or self.sig_longa1 or self.sig_shorta1
                or self.sig_long_dec or self.sig_short_dec
                or self.sig_longx1 or self.sig_shortx1):
            self.order_datetime = self.dtdt.datetime(0)  # 订单时间

        # 入场开仓准备
        if self.sig_long or self.sig_short:
            # self.broker.setcommission(automargin=self.p.automargin)  # 设置初始保证金比率
            self.entry_order['入场价格'] = self.dtclose[0]  # 入场价格
            self.entry_price = self.dtclose[0]  # 入场价格
            self.entry_price_begin = self.entry_price  # 开始入场价格
            self.turtleunits = 1  # 加仓次数
            self.order_this_bar = 1  # 标记该周期的交易状态
            self.bar_executed = len(self)  # 记录当前交易的bar序列
            self.p_po = (self.p_po + 0.0000) * 1.000  # 加减仓幅度
            self.mpwa = self.p_pw  # 盈利千分比
            self.mpla = self.p_pw  # 亏损千分比
        # 买入开仓价格
        if self.sig_long:
            t_enter += ',买入'
            self.sig_ref1 = self.position_flag = 1  # 记录开仓信号
            self.p_ok = abs(self.p_ok + 0.001)
            self.entry_mpok = self.p_ok

            self.radd = self.entry_price * (1 + self.p_pw)
            self.lout = self.entry_price / (1 + self.p_pl)
        # 卖出开仓价格
        elif self.sig_short:
            t_enter += ',卖出'
            self.sig_ref1 = self.position_flag = -1  # 记录开仓信号
            self.p_ok = -abs(self.p_ok + 0.001)
            self.entry_mpok = self.p_ok
            # self.radd = self.entry_price * (1 - self.p_pw)
            # self.lout = self.entry_price * (1 + self.p_pl)
            self.radd = self.entry_price / (1 + self.p_pw)
            self.lout = self.entry_price * (1 + self.p_pl)
        # 入场开仓下单及日志
        if self.sig_long or self.sig_short:
            self.myorder = self.order_target(self.p_ok)
            if self.myorder and hasattr(self.myorder, 'size'):
                t_enter += ',开仓中:{:d}'.format(self.myorder.size)
            else:
                t_enter += ',开仓中'
            t_enter += ',持仓:{:}'.format(self.position.size)
            t_enter += ',price:{:.2f}'.format(self.dtclose[0])
            t_enter += ',总资产:{:.2f}'.format(assets)
            # self.log(t_enter)
            pass

        # 持仓加仓准备
        if self.sig_longa1 or self.sig_shorta1:
            self.entry_order['上次入场价格'] = (self.entry_order['加仓价格'] if '加仓价格' in self.entry_order else self.entry_order['入场价格'])  # 上次加仓价格
            self.entry_order['加仓价格'] = self.dtclose[0]  # 加仓价格
            self.entry_price_ref1 = self.entry_price
            self.entry_price = self.dtclose[0]  # 入场价格
            self.turtleunits += 1  # 加仓次数加1
            self.order_this_bar = 1  # 标记该周期的交易状态
            self.bar_executed = len(self)  # 记录当前交易的bar序列
            mpe_r1_ = abs(self.entry_price - self.entry_price_ref1) / self.entry_price_ref1  # 当前入场价与上次入场价之间的涨跌幅度
            # mpr_ = max(mpe_r1_, mpr_)  # 当出现跳空缺口时,是否调整盈利预期
            mpe_r1_ = abs(self.entry_price - self.entry_price_ref1) / self.entry_price_ref1  # 当前入场价与上次入场价之间的涨跌幅度
            automargin = self.broker.getcommissioninfo(data=self.data).p.automargin  # 获取保证比率*合约乘数
            automargin_re = automargin * (mpe_r1_ / self.p_pl) if mpe_r1_ else automargin  # 调整保证金比率, 是否根据入场价之间的涨跌幅度调整保证金比率
            # self.broker.setcommission(automargin=automargin_re)  # 设置保证金比率
            if self.ppos_profit_ref1 >= 0:
                # 连续亏损时,减少下次开仓比率
                if self.numlosst > 1:
                    self.p_ok = self.p_ok / (1 + self.p_po)
                self.numlosst = 0
                self.p_ok = (self.p_ok * (1 + (self.p_po)))  # 上一笔交易盈利时，增加仓位
            else:
                self.p_ok = (self.p_ok * (1 - (self.p_po)))  # 上一笔交易亏损时，减少仓位
                pass
            if True:
                if self.mpwa > self.mpla:  # 盈利比>亏损比时,减少盈利比
                    # self.mpwa = self.mpwa / (1 + abs(self.mpwa - self.mpla) / abs(self.mpwa + self.mpla))
                    self.mpwa = self.mpwa / (1 + self.p_pp)  # 减少盈利比
                    self.mpla = self.mpla * (1 + self.p_pp)  # 增加亏损比
                    pass
                elif self.mpla > self.mpwa:  # 亏损比>盈利比时,减少亏损比
                    # self.mpla = self.mpla / (1 + abs(self.mpwa - self.mpla) / abs(self.mpwa + self.mpla))
                    self.mpla = self.mpla / (1 + self.p_pp)  # 减少亏损比
                    self.mpwa = self.mpwa * (1 + self.p_pp)  # 增加盈利比
                    pass
                elif abs(self.mpla - self.mpwa) * 2 / abs(self.mpla + self.mpwa) < abs(self.p_pp):  # 亏损比=盈利比时,同时减少盈利和亏损比
                    self.mpwa = self.mpwa / (1 + self.p_pp)  # 减少盈利比
                    self.mpla = self.mpla / (1 + self.p_pp)  # 减少亏损比
                    pass

        # 多头加仓价格
        if self.sig_longa1:
            t_add += ',买入'
            self.p_ok = abs(self.p_ok)

            self.radd = self.entry_price * (1 + self.mpwa)
            self.lout = self.entry_price / (1 + self.mpla)
        # 空头加仓价格
        if self.sig_shorta1:
            t_add += ',卖出'
            self.p_ok = -abs(self.p_ok)

            # self.radd = self.entry_price * (1 - self.p_pw)
            # self.lout = self.entry_price * (1 + self.p_pl)
            self.radd = self.entry_price / (1 + self.mpwa)
            self.lout = self.entry_price * (1 + self.mpla)
        # 加仓下单及日志
        if self.sig_longa1 or self.sig_shorta1:
            self.myorder = self.order_target(self.p_ok)  # 加仓中
            if self.myorder and hasattr(self.myorder, 'size'):
                t_add += ',加仓中:{:d}'.format(self.myorder.size)
            else:
                t_add += ',加仓中'
            t_add += ',持仓:{:}'.format(self.position.size)
            t_add += ',price:{:.2f}'.format(self.dtclose[0])
            t_add += ',总资产:{:.2f}'.format(assets)
            # self.log(t_add)
            pass

        # 多头减仓头寸
        if self.sig_long_dec:
            self.p_ok = abs(self.p_pok_min)  # 保留最小头寸
        # 空头减仓头寸
        if self.sig_short_dec:
            self.p_ok = -abs(self.p_pok_min)  # 保留最小头寸
        # 减仓离场下单及日志
        if self.sig_long_dec or self.sig_short_dec:
            self.order_this_bar = 1  # 标记该周期的交易状态
            self.sig_long_keyPoint = False  # 清除信号
            self.sig_short_keyPoint = False  # 清除信号
            self.myorder = self.order_target(self.p_ok)
            t_dec += ',多头' if self.sig_longx1 else ',空头'
            t_dec += ',减仓中:{:}'.format(self.position.size)
            t_dec += ',price:{:.2f}'.format(self.dtclose[0])
            t_dec += ',总资产:{:.2f}'.format(assets)
            # self.log(t_dec)
            pass

        # 多头清仓离场准备
        if self.sig_longx1:
            self.ppos_profit_ref1 = ((self.exit_price - self.entry_price_begin) / self.entry_price_begin)  # 计算上一笔交易盈亏幅度
        # 空头清仓离场准备
        if self.sig_shortx1:
            self.ppos_profit_ref1 = ((self.entry_price_begin - self.exit_price) / self.entry_price_begin)  # 计算上一笔交易盈亏幅度
        # 清仓离场价格及头寸 SEXIT CLOSE
        if self.sig_longx1 or self.sig_shortx1:
            # 盈利后,减少下次开仓比率
            if self.turtleunits > 1:
                self.p_ok = (self.p_ok / self.turtleunits)
            self.p_ok = self.p_ok if self.p_ok > self.p_pok_min else self.p_pok_min
            self.exit_price = self.dtclose[0]
            self.position_flag = 0  # 清仓后头寸方向为0
            self.turtleunits = 0  # 加仓次数
            self.numlosst += 1  # 统计连续亏损次数
            self.order_this_bar = 1  # 标记该周期的交易状态
            self.mbstop = 0
        # 清仓离场下单及日志
        if self.sig_longx1 or self.sig_shortx1:  # 平仓离场
            # 全部平仓
            self.myorder = self.close()
            t_exit += ',多头' if self.sig_longx1 else ',空头'
            t_exit += ',平仓中:{:}'.format(self.position.size)
            t_exit += ',price:{:.2f}'.format(self.dtclose[0])
            t_exit += ',总资产:{:.2f}'.format(assets)
            # self.log(t_exit)
            pass

    def stop(self):
        """测略结束时，多用于参数调优"""
        # self.log(' 参数 pw:{:2d} '.format(self.p.pw)
        #          + ' pl:{:2d} '.format(self.p.pl)
        #          + ' 期末资金: {:.2f} '.format(self.broker.getvalue())
        #          , doprint=True)


class Statistics():
    """策略统计,成交记录"""
    # 记录每笔交易的成交与账户持仓等信息
    trade_record = {
        'datetime': [],  # 记录每笔交易发生的时间
        '交易类型': [],  # 交易类型 开多,开空, 平多,平空
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


"""-------主函数---------"""
if __name__ == '__main__':
    runstrat()
