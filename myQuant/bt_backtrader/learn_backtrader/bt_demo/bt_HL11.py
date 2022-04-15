import os
import backtrader as bt
import argparse
import pandas as pd
import numpy as np
import time
from enum import Enum

DT_FILE_PATH = "datas\\SQRB13-5m-20121224-20220330.csv"
DT_DTFORMAT = '%Y-%m-%d %H:%M:%S'
DT_START, DT_END = '2012-01-01', '2013-02-01'
DT_TIMEFRAME = 'minutes'  # 重采样更大时间周期
DT_COMPRESSION = 15  # 合成周期的bar数
DT_PRINTLOG = False  # 是否打印日志
DT_PLOT = False  # 是否绘图,还可提供绘图参数:'style="candle"'
DT_QUANTSTATS = True  # 是否使用 quantstats 分析测试结果
DT_OPTS = True  # 是否参数调优
DT_RPP = [5, 1, 10]  # 参数
DT_SPP = [17, 10, 20]  # 参数


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for Order Target')

    parser.add_argument('--data', required=False,
                        default=DT_FILE_PATH,
                        help='Specific data to be read in')
    parser.add_argument('--dtformat', required=False, default=DT_DTFORMAT,
                        help='Ending date in data datetime format')
    parser.add_argument('--fromdate', required=False, default=DT_START,
                        help='Starting date in `dtformat` format')
    parser.add_argument('--todate', required=False, default=DT_END,
                        help='Ending date in `dtformat` format')
    parser.add_argument('--timeframe', required=False, default=DT_TIMEFRAME,
                        choices=['minutes', 'daily', 'weekly', 'monthly'],
                        help='重新采样到的时间范围')
    parser.add_argument('--compression', required=False, type=int, default=DT_COMPRESSION,
                        help='将 n 条压缩为 1, 最小周期为原数据周期')
    parser.add_argument('--opts', required=False, type=bool, default=DT_OPTS,
                        help='策略优化')
    parser.add_argument('--quantstats', required=False, type=int, default=DT_QUANTSTATS,
                        help='是否使用 quantstats 分析测试结果')
    parser.add_argument('--maxcpus', '-m', type=int, required=False, default=15,
                        help=('Number of CPUs to use in the optimization'
                              '\n  - 0 (default): 使用所有可用的 CPU\n   - 1 -> n: 使用尽可能多的指定\n'))
    parser.add_argument('--no-optdatas', action='store_true', required=False, help='优化中不优化数据预加载')
    parser.add_argument('--no-optreturn', action='store_true', required=False,
                        help='不要优化返回值以节省时间,这避免了回传大量生成的数据，例如指标在回溯测试期间生成的值')

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const=True, default=DT_PLOT,
                        help=('绘制应用传递的任何 kwargs 的读取数据\n'
                              '\n''例如:\n''\n''  --plot style="candle" (to plot candles)\n'))
    parser.add_argument("-f", "--file", default="file")  # 接收这个-f参数
    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


def runstrat(args=None):
    args = parse_args(args)
    dkwargs = dict()

    file_path = dt_start = dt_end = dt_format = dt_dtformat = dt_tmformat = ""

    if args.dtformat is not None:
        dt_format = args.dtformat
        dt_dtformat = dt_format[:dt_format.find('%d') + len('%d')]
        dt_tmformat = dt_format[dt_format.find('%H'):]
    if args.fromdate is not None:
        dt_start = bt.datetime.datetime.strptime(args.fromdate, dt_dtformat)
    if args.todate is not None:
        dt_end = bt.datetime.datetime.strptime(args.todate, dt_dtformat)
    if args.data is not None:
        file_path = args.data

    myQuant_ROOT = os.getcwd()[:os.getcwd().find("bt_backtrader\\") + len("bt_backtrader\\")]  # 获取项目中相对根路径
    file_path_abs = os.path.join(myQuant_ROOT, file_path)  # 文件路径
    print(file_path_abs)
    print("dt_format:", dt_format, "dt_start:", dt_start, "dt_end:", dt_end)
    if not os.path.exists(file_path_abs):
        raise Exception("数据源文件未找到！" + file_path_abs)

    dkwargs['fromdate'] = dt_start
    dkwargs['todate'] = dt_end
    dkwargs['dtformat'] = dt_format
    # dkwargs['tmformat'] = dt_tmformat

    print(dkwargs)
    # 加载数据
    df = pd.read_csv(filepath_or_buffer=file_path_abs,
                     # parse_dates={'datetime': ['date', 'time']},  # 日期和时间分开的情况
                     parse_dates=['datetime'],
                     index_col='datetime',
                     infer_datetime_format=True,
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
    # 增加一列openinterest
    df['openinterest'] = 0.00
    # 取出特定的列
    df = df[['open', 'high', 'low', 'close', 'volume']]
    # 列名修改成指定的
    df.rename(columns={"volume": "vol"}, inplace=True)

    tframes = dict(
        minutes=bt.TimeFrame.Minutes,
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months)
    # data = bt.feeds.GenericCSVData(dataname=file_path, **dkwargs)
    # 使用pandas数据源创建交易数据集
    data = (bt.feeds.PandasData(dataname=df, fromdate=dt_start, todate=dt_end))
    # 重采样到更大时间框架
    if args.timeframe and args.compression:
        data.resample(timeframe=tframes[args.timeframe], compression=args.compression)

    cerebro = bt.Cerebro(stdstats=False)

    cerebro.adddata(data)
    # 设置投资金额100000.0
    cerebro.broker.setcash(100000.0)

    # <editor-fold desc="折叠代码:交易手续费设置">
    cerebro.broker.setcommission(
        # 交易手续费，根据margin取值情况区分是百分比手续费还是固定手续费
        # commission=0.0015,
        commission=2.4,
        # 期货保证金，决定着交易费用的类型,只有在stocklike=False时起作用
        margin=0,
        # 乘数，盈亏会按该乘数进行放大
        mult=10.0,
        # 交易费用计算方式，取值有：
        # 1.CommInfoBase.COMM_PERC 百分比费用
        # 2.CommInfoBase.COMM_FIXED 固定费用
        # 3.None 根据 margin 取值来确定类型
        commtype=bt.CommInfoBase.COMM_FIXED,
        # 当交易费用处于百分比模式下时，commission 是否为 % 形式
        # True，表示不以 % 为单位，0.XX 形式；False，表示以 % 为单位，XX% 形式
        percabs=True,
        # 是否为股票模式，该模式通常由margin和commtype参数决定
        # margin=None或COMM_PERC模式时，就会stocklike=True，对应股票手续费；
        # margin设置了取值或COMM_FIXED模式时,就会stocklike=False，对应期货手续费
        stocklike=False,
        # 计算持有的空头头寸的年化利息
        # days * price * abs(size) * (interest / 365)
        interest=0.0,
        # 计算持有的多头头寸的年化利息
        interest_long=False,
        # 杠杆比率，交易时按该杠杆调整所需现金
        leverage=1.0,
        # 自动计算保证金
        # 如果 False, 则通过margin参数确定保证金
        # 如果automargin<0, 通过mult*price确定保证金
        # 如果automargin>0, 如果automargin*price确定保证金
        automargin=10 * 0.10,
        # 交易费用设置作用的数据集(也就是作用的标的)
        # 如果取值为None，则默认作用于所有数据集(也就是作用于所有assets)
        name=None
    )
    # </editor-fold>

    strats = None
    # 参数调优
    if args.opts:
        result = None
        # 为Cerebro引擎添加策略, 优化策略
        strats = cerebro.optstrategy(
            TestStrategy,
            rpp=range(DT_RPP[1], DT_RPP[2]),
            spp=range(DT_SPP[1], DT_SPP[2]),
            printlog=False,
        )
        # 添加分析指标
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timeReturn', timeframe=bt.TimeFrame.Years)  # 此分析器通过查看时间范围的开始和结束来计算回报
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")  # 使用对数方法计算的总回报、平均回报、复合回报和年化回报
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")  # 回撤
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")  # 夏普率
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="tradeAnalyzer")  # 提供有关平仓交易的统计信息（也保留未平仓交易的数量）
        # clock the start of the process
        tstart = time.perf_counter()
        # Run over everything
        # result = cerebro.run()
        result = cerebro.run(
            maxcpus=args.maxcpus,
            optdatas=not args.no_optdatas,  # optdatas（默认值：True)如果和优化（以及系统可以和使用），数据预加载将只在主进程中完成一次，以节省时间和资源。
            optreturn=not args.no_optreturn,  # optreturn（默认值：True)如果优化结果不是完整的对象（以及所有数据、指标、观察器等），而是具有以下属性的对象 在大多数情况下，只有分析器和哪些参数是评估策略性能所需的东西。如果需要对（例如）指标的生成值进行详细分析，请将其关闭
            # optreturn=False,
            # stdstats=False,
        )
        # clock the end of the process
        tend = time.perf_counter()
        # print out the result
        print('Time used:', str(tend - tstart))

        print("\n--------------- 分析结果 -----------------")

        # 每个策略实例的结果以列表的形式保存在列表中。
        # 优化运行模式下，返回值是列表的列表,内列表只含一个元素，即策略实例
        res_list = [[]]
        res_timereturn_title = []  # 列标题

        timeReturn = result[0][0].analyzers.timeReturn.get_analysis()  # timeReturn 分析引用
        for k, v in timeReturn.items():
            res_timereturn_title.append('{:%Y-%m}'.format(k))

        for x in result:
            trade = x[0].analyzers.tradeAnalyzer.get_analysis()  # 交易分析引用
            returns = x[0].analyzers.returns.get_analysis()  # 回报分析引用
            drawdown = x[0].analyzers.drawdown.get_analysis()  # 回撤分析引用
            sharpe = x[0].analyzers.sharpe.get_analysis()  # sharpe分析引用
            timeReturn = x[0].analyzers.timeReturn.get_analysis()  # timeReturn 分析引用

            row = [
                x[0].p.rpp,  # 参数
                x[0].p.spp,  # 参数
                returns['rtot'],  # 总复合回报
                (trade['won']['total']) / (trade['lost']['total'] + trade['won']['total']),  # 胜率
                returns['rnorm100'],  # 以 100% 表示的年化归一化回报
                drawdown['max']['drawdown'],  # 最大回撤
                sharpe['sharperatio'],  # 夏普率
                (((trade['pnl']['gross']['total']) - (trade['pnl']['net']['total'])) / (trade['pnl']['gross']['total'])),  # 手续费比净盈亏
                trade['total']['total'],  # 交易次数
                trade['pnl']['net']['total'],  # 帐户余额含手续费
            ]
            res_timereturn_row = list(timeReturn.values())  # 月度或年度复合回报,由参数timeframe=bt.TimeFrame.Months控制
            row.extend(res_timereturn_row)  # 月度复合回报
            # 变量是浮点数时,且<10时,%比显示保留5位整数1位小数且*100,>10时保留8位整数2位小数,不是浮点数时保留5位整数
            row_3d = [(('{:5.1f}' if abs(i) < 10 else '{:8.2f}') if isinstance(i, float) else '{:5}').format(i * 100 if (abs(i) < 10 and isinstance(i, float)) else i) for i in row]
            res_list.append(row_3d)  # 添加到返回列表

        # 结果转成dataframe
        columns = ['rpp', 'spp', 'rtot%', 'won%', 'rnorm%', 'maxDD%', 'sharpe', 'comm%', 'total', 'net']
        columns_all = columns.copy()
        columns_all.extend(res_timereturn_title)  # 将列标题添加到columns列表尾部
        res_df = pd.DataFrame(res_list, dtype='float', columns=columns_all)
        res_df = res_df.dropna(how='any', axis=0)  # 删除所有带NaN的行
        pd.set_option('precision', 3)  # 显示小数点后的位数
        pd.set_option('display.min_rows', 300)  # 确定显示的最小行有多少
        pd.set_option('display.max_columns', 20)  # 确定显示最大列多少
        pd.set_option('expand_frame_repr', False)  # True就是可以换行显示。设置成False的时候不允许换行
        pd.set_option('display.width', 180)  # 设置打印宽度(**重要**)
        res_df = res_df.sort_values(by='rtot%')  # 按总复合回报排序
        res_df[res_df.columns[:5]].info()  # 显示前几列的数据类型
        print(res_df.loc[:, columns])  # 显示指定列
        res_df.to_csv('result.csv', sep='\t', float_format='%.3f')  # 保存分析数据到文件
    # 回测分析
    else:
        # 添加观测器,绘制时显示
        cerebro.addobserver(bt.observers.Broker)
        cerebro.addobserver(bt.observers.Trades)
        cerebro.addobserver(bt.observers.BuySell)
        cerebro.addobserver(bt.observers.DrawDown)
        # cerebro.addobserver(bt.observers.TimeReturn)
        # 添加分析指标
        cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualReturn')  # 返回年初至年末的年度收益率
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawDown')  # 计算最大回撤相关指标
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns', tann=252)  # 计算年化收益：日度收益
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyFolio')  # 添加PyFolio
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpeRatio', timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0)  # 计算年化夏普比率：日度收益
        cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='sharpeRatio_A')
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timeReturn', )  # 添加收益率时序

        # 添加策略和参数
        cerebro.addstrategy(TestStrategy, rpp=DT_RPP[0], spp=DT_SPP[0], printlog=DT_PRINTLOG)

        # 引擎运行前打印期出资金
        print('组合期初资金: %.2f' % cerebro.broker.getvalue())
        # 启动回测
        result = cerebro.run()
        # 引擎运行后打期末资金
        print('组合期末资金: %.2f' % cerebro.broker.getvalue())
        # 提取结果
        print("\n--------------- 累计收益率 -----------------")
        annualReturn = result[0].analyzers.annualReturn.get_analysis()
        print(" Cumulative Return: {:.2f}".format(sum(annualReturn.values())))
        print("\n--------------- 年度收益率 -----------------")
        # print(' 收益率k,v', get_analysis.items())
        for k, v in annualReturn.items():
            print((" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v), end='')
        print("\n--------------- 最大回撤 -----------------")
        drawDown = result[0].analyzers.drawDown.get_analysis()
        for k, v in drawDown.items():
            if not isinstance(v, dict):
                t = (" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v)
                print(t, end='')
            else:
                for kk, vv in v.items():
                    t = (" [{:},{:.2f}]" if isinstance(vv, float) else " [{:},{:}]").format(kk, vv)
                    print(t, end='')
        print("\n--------------- 年化收益：日度收益 -----------------")
        returns = result[0].analyzers.returns.get_analysis()
        for k, v in returns.items():
            print((" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v), end='')
        print("\n--------------- 年化夏普比率：日度收益 -----------------")
        sharpeRatio = (result[0].analyzers.sharpeRatio.get_analysis())
        for k, v in sharpeRatio.items():
            print((" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v), end='')
        print("\n--------------- SharpeRatio_A -----------------")
        sharpeRatio_A = result[0].analyzers.sharpeRatio_A.get_analysis()
        for k, v in sharpeRatio_A.items():
            print((" [{:},{:.2f}]" if isinstance(v, float) else " [{:},{:}]").format(k, v), end='')
        print("\n--------------- test end -----------------")
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
        pnl = pd.Series(result[0].analyzers.timeReturn.get_analysis())
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
        portfolio_stats = result[0].analyzers.getbyname('pyFolio')
        returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
        returns.index = returns.index.tz_convert(None)
        import quantstats
        # 将分析指标保存到HTML文件
        quantstats.reports.html(returns, output='stats.html',
                                title=DT_FILE_PATH + 'rpp:{:} spp:{:}'.format(DT_RPP, DT_SPP))
        print("quantstats 测试分析结果已保存至目录所在文件 quantstats-tearsheet.html")
        # 使用quantstats 分析工具并保存到HTML文件


class UseTarget(Enum):
    """枚举开仓类型"""
    USE_TARGET_SIZE = 0  # 成交量
    USE_TARGET_VALUE = 1  # 目标金额
    USE_TARGET_PERCENT = 2  # 百分比


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None, printlog=None):
        # 记录策略的执行日志
        if self.p.printlog or printlog:
            dt = dt or self.datas[0].datetime.datetime(0)
            # 时间断点调试,调试条件 self.datas[0].datetime.datetime(0) >= bt.datetime.datetime.strptime('2018-01-23 14:05:00','%Y-%m-%d %H:%M:%S')
            # print('%s, %s' % (dt.isoformat(), txt))
            print('%s, %s' % (dt.strftime('%a %Y-%m-%d %H:%M:%S'), txt))

    params = dict(
        rpp=18,  # 盈利千分比
        spp=17,  # 亏损千分比
        rspp=5,  # 盈亏千分比
        poskk=10,  # 入场开仓单位 按(数量,金额,百分比)下单
        posadp=0,  # 加减仓幅度百分比
        posmax=50,  # 最大开仓单位
        ocjk=1,  # CLOSE与OPEN的间隔
        sspp=0,  # 最大回撤千分比
        addLongOrShort=0,  # 加仓方向addLongOrShort=0无限制,>0时只有多头加仓,<0时只有空头加仓
        valid=None,  # 订单生效时间
        printlog=False,  # 是否打印日志
        use_target=UseTarget.USE_TARGET_PERCENT,  # use_target_percent 按目标百分比下单 use_target_size=False,  # 按目标数量下单 use_target_value=False,  # 按目标金额下单
    )

    def __init__(self):
        # super().__init__(*args, **kwargs)
        # self.opts = opts  # 启动参数
        self.mprs = self.p.rspp / 1000  # 盈亏千分比
        self.mpr = self.p.rpp / 1000  # 盈利千分比
        self.mps = self.p.spp / 1000  # 亏损千分比
        self.mpposad = self.p.posadp / 100  # 加减仓幅度百分比
        self.mposkk = self.p.poskk  # 开仓单位
        self.mpposmin = self.p.poskk  # 最小开仓单位
        self.mpposmax = self.p.posmax  # 最大开仓单位
        self.myentryprice_begin = 0.0  # 初始入场价格
        self.myentryprice = 0.0  # 入场价格
        self.myexitprice = 0.0  # 离场价格
        self.buyorderthisbar = 0  # 该周期是否有交易 0没有,1有
        self.bar_executed = 0  # 记录当前交易的bar序列
        self.turtleunits = 0  # 加仓次数
        self.numlosst = 0  # 统计连续亏损次数
        self.ppunit = 1  # 交易手数比率
        self.positionflag = 0  # 仓位状态 0表示没有仓位，1表示持有多头， -1表示持有空头
        self.radd = 0  # 盈利加仓价格
        self.sexit = 0  # 亏损退出价格
        self.sig_ref1 = 0  # 记录上一次入场信号 1多头,-1空头,0无
        self.sig_long = 0  # 多头条件
        self.sig_short = 0  # 空头条件
        self.sig_longa1 = 0  # 多头加仓条件
        self.sig_shorta1 = 0  # 空头条件
        self.sig_longx1 = 0  # 多头离场条件
        self.sig_shortx1 = 0  # 空头离场条件
        self.mbstop = 0  # 是否触发回撤止损
        self.pl_sum = 0  # 累计连续亏损百分比
        self.dtopen_month = 0.0  # 记录每月开盘价
        self.initial_amount = 0.0  # 初始金额

        # 建立对于DataFeed的Open/Close价格的引用参数
        self.dtdate = self.datas[0].datetime.date
        self.dtopen = self.datas[0].open
        self.dtclose = self.datas[0].close
        self.dthigh = self.datas[0].high
        self.dtlow = self.datas[0].low

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
        if not trade.isclosed:
            return
        t = 'notify_trade:'
        t += ',盈亏, {:.2f},comm {:.2f}, NET {:.2f}'.format(
            trade.pnl,  # 盈亏
            (trade.pnl - trade.pnlcomm),  # 手续费
            trade.pnlcomm)  # 盈亏含手续费
        t += ',add:{:.2f}'.format(self.radd)
        t += ',exit:{:.2f}'.format(self.sexit)
        t += ',open_m3:{:}'.format(self.dtopen_month)
        t += ',总资产:{:.2f}'.format(self.broker.getvalue())
        # t += ',回撤:{:.2f}'.format(self.stats.drawdown.drawdown[0])
        # t += ',收益率:{:.3f}'.format(self.stats.timereturn.line[0])
        t += ',开仓比:{:.0f}%'.format(self.mposkk)

        self.log(t)

    def notify_order(self, order):
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
        t += ',exit:{:.2f}'.format(self.sexit)
        t += ',open_m3:{:}'.format(self.dtopen_month)
        t += ',可用资金:{:.2f}'.format(self.broker.getcash())
        t += ',持仓市值:{:.2f}'.format(self.broker.getvalue(datas=[self.data]))
        t += ',总资产:{:.2f}'.format(self.broker.getvalue())
        t += ',开仓比:{:.0f}%'.format(self.mposkk)

        self.log(t)
        if not order.alive():
            self.myorder = None  # 表示没有订单待处理

    def order_target(self, size=None, data=None):
        """订单开仓头寸管理"""
        size = size if size else self.mposkk
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
        margin = comminfo.get_margin(self.dtclose[0]) * 1.01  # 最低开仓保证金
        margin_cash = self.broker.getvalue(datas=[self.data])  # 持仓头寸占用资金
        # margin = bt.Order.comminfo.get_margin(self.dtclose[0])  # 最低开仓保证金
        get_cash = abs(self.broker.getcash())  # 可用资金
        get_cash_value = abs(self.broker.getvalue())  # 帐户总资金
        sign = np.sign(self.mposkk)  # 取正负符号
        open_profit = sign * self.position.size * (self.position.price - self.dtclose[0])  # 浮动盈亏
        total_return = (get_cash_value - self.initial_amount) / self.initial_amount  # 总回报率

        # 按成交量下单
        if self.p.use_target == UseTarget.USE_TARGET_SIZE:
            poskkcash = margin * abs(size)  # 开仓金额
            posmincash = min(1, int(round((get_cash // margin))))  # 最小开仓金额
            posmaxcash = min(max(1, (margin * self.mpposmax)), int(round((get_cash // margin))))  # 最大开仓金额
            if size > 0:
                size = (abs(self.position.size) + self.mpposmin)
            elif size < 0:
                size = -(abs(self.position.size) + self.mpposmin)

            # 限定使用资金的范围
            poskkcash = sign * (  # sign 为开仓方向
                get_cash if (posmincash > get_cash)  # 最小开仓金额>可用金额时,使用可用金额
                else (  # 最小开仓金额<可用金额时
                    posmincash if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,使用最小开仓金额
                    else (posmaxcash if (abs(poskkcash) > posmaxcash)  # 开仓金额>最大开仓金额时,使用最大开仓金额
                          else poskkcash)))
            target = int(round(poskkcash // margin))

            self.myorder = self.order_target_size(target=target)
            self.mposkk = size

        else:

            # 按目标金额下单
            if self.p.use_target == UseTarget.USE_TARGET_VALUE:
                poskkcash = (margin_cash // self.turtleunits) + self.mposkk if self.turtleunits > 1 else margin_cash + self.mposkk  # 开仓金额
                posmincash = min(margin * 1.1, get_cash)  # 最小开仓金额
                posmaxcash = min(max(margin * 1.1, self.mpposmax), get_cash)  # 最大开仓金额
                # 限定使用资金的范围
                poskkcash = sign * (  # sign 为开仓方向
                    get_cash if (posmincash > get_cash)  # 最小开仓金额>可用金额时,使用可用金额
                    else (  # 最小开仓金额<可用金额时
                        posmincash if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,使用最小开仓金额
                        else (posmaxcash if (abs(poskkcash) > posmaxcash)  # 开仓金额>最大开仓金额时,使用最大开仓金额
                              else poskkcash)))
                self.myorder = self.order_target_value(target=poskkcash)
                self.mposkk = poskkcash

            # 按目标百分比下单
            elif self.p.use_target == UseTarget.USE_TARGET_PERCENT:
                posmincash = min(margin * 1.1, get_cash)  # 最小开仓金额
                posmaxcash = min(max(margin * 1.1, (get_cash * self.mpposmax)), get_cash)  # 最大开仓金额
                percent = (margin_cash / get_cash)  # 持仓头寸占可用资金比率
                # percent = (margin_cash / get_cash_value)  # 持仓头寸占总资金比率
                percent = percent if percent else (size / 100)  # 首次开仓使用size%参数
                if size > 0:  # 开多仓
                    percent = (abs(percent) * (1 + self.mpposad))
                elif size < 0:  # 开空仓
                    percent = -(abs(percent) * (1 + self.mpposad))
                else:  # 不开仓
                    pass

                # poskkcash = percent * (get_cash - open_profit)  # 可用资金百分比交易
                poskkcash = percent * (get_cash - open_profit - self.initial_amount) if total_return > 100 else percent * (get_cash - open_profit)  # 总盈利>初始金额时,使用盈利金额交易
                # poskkcash = percent * (get_cash_value - open_profit)  # 帐户总资金百分比交易

                # 限定使用资金的范围
                poskkcash = sign * (  # sign 为开仓方向
                    get_cash if (posmincash > get_cash)  # 最小开仓金额>可用金额时,使用可用金额
                    else (  # 最小开仓金额<可用金额时
                        posmincash if (abs(poskkcash) <= posmincash)  # 开仓金额<最小开仓金额时,使用最小开仓金额
                        else (posmaxcash if (abs(poskkcash) > posmaxcash)  # 开仓金额>最大开仓金额时,使用最大开仓金额
                              else poskkcash)))

                percent = sign * ((abs(poskkcash) + margin_cash) / get_cash_value)  # 计算占用账户总资金的百分比
                # percent = sign * (abs(poskkcash) / get_cash)  # 计算占可用资金百分比 self.myorder = self.order_target_percent(target=percent)
                self.myorder = self.order_target_percent(target=percent)
                self.mposkk = percent * 100

        return self.myorder

    def next(self):
        # 记录收盘价
        # self.log('Close, %.2f' % self.dtclose[0])
        # if (round(self.dtdate(0).month // 3) % 4) != (round(self.dtdate(-1).month // 3) % 4):  # 记录每个季度open价
        if (round(self.dtdate(0).month)) != (round(self.dtdate(-1).month)):  # 记录每个月open价
            self.dtopen_month = self.datas[0].open[0]
        self.buyorderthisbar = 0  # 标记该周期的交易状态

        # 如果有订单正在挂起，不操作
        if self.myorder:
            return
        # 多头入场条件
        self.sig_long = (
                not self.position  # 空仓时
                and (self.dtclose[0] > self.dtopen[0])
        )
        # 空头入场条件
        self.sig_short = (
                not self.position  # 空仓时
                and (self.dtclose[0] < self.dtopen[0])
        )
        # 多头加仓条件
        self.sig_longa1 = (self.positionflag == 1
                           and (self.dtlow[0] > self.dtopen_month)
                           and (self.dthigh[0] > self.dtlow[0])
                           and (self.dtclose[0] >= self.radd)
                           and self.buyorderthisbar == 0)
        # 空头加仓条件
        self.sig_shorta1 = (self.positionflag == -1
                            and (self.dtlow[0] < self.dtopen_month)
                            and (self.dthigh[0] > self.dtlow[0])
                            and (self.dtclose[0] <= self.radd)
                            and self.buyorderthisbar == 0)
        # 多头离场条件 添加OPEN价离场条件
        self.sig_longx1 = (self.positionflag == 1) and self.dthigh[0] > self.dtlow[0] and (
                self.dtclose[0] <= self.sexit or self.dtopen[0] <= self.sexit)
        # 空头离场条件 添加OPEN价离场条件
        self.sig_shortx1 = ((self.positionflag == -1) and self.dthigh[0] > self.dtlow[0] and (
                self.dtclose[0] >= self.sexit or self.dtopen[0] >= self.sexit))

        # t = 'next:'
        t_enter = t_add = t_exit = 'next:'
        assets = self.broker.getvalue()

        # t += ',持仓:{:d}'.format(self.position.size)
        # 如果没有持仓且可用资产>0 时则准备入场
        if not self.position and self.position.size == 0 and (assets > 0):

            if self.sig_long or self.sig_short:
                self.myentryprice = self.dtclose[0]  # 入场价格
                self.myentryprice_begin = self.myentryprice  # 开始入场价格
                self.turtleunits = 1  # 加仓次数
                self.buyorderthisbar = 1  # 标记该周期的交易状态
                self.bar_executed = len(self)  # 记录当前交易的bar序列

            if self.sig_long:  # 买入
                t_enter += ',买入'
                self.sig_ref1 = self.positionflag = 1  # 记录开仓信号
                self.mposkk = abs(self.mposkk + 0.0001)

                self.radd = self.myentryprice * (1 + self.mpr)
                self.sexit = self.myentryprice / (1 + self.mps)

            elif self.sig_short:  # 卖出
                t_enter += ',卖出'
                self.sig_ref1 = self.positionflag = -1  # 记录开仓信号
                self.mposkk = -abs(self.mposkk * 1 + 0.0001)

                # self.radd = self.myentryprice * (1 - self.mpr)
                # self.sexit = self.myentryprice * (1 + self.mps)
                self.radd = self.myentryprice / (1 + self.mpr)
                self.sexit = self.myentryprice * (1 + self.mps)

            # 入场开仓
            if self.sig_long or self.sig_short:
                self.myorder = self.order_target(self.mposkk)
                if self.myorder and hasattr(self.myorder, 'size'):
                    t_enter += ',开仓中:{:d}'.format(self.myorder.size)
                else:
                    t_enter += ',开仓中'
                t_enter += ',持仓:{:}'.format(self.position.size)
            if self.buyorderthisbar == 1:
                t_enter += ',price:{:.2f}'.format(self.dtclose[0])
                t_enter += ',总资产:{:.2f}'.format(assets)
                # self.log(t_enter)
        # 有持仓时
        else:
            # 盈利加仓
            if self.sig_longa1 or self.sig_shorta1:
                self.myentryprice = self.dtclose[0]  # 入场价格
                self.turtleunits += 1  # 加仓次数加1
                self.buyorderthisbar = 1  # 标记该周期的交易状态
                self.bar_executed = len(self)  # 记录当前交易的bar序列

            # 多头加仓
            if self.sig_longa1:
                t_add += ',买入'
                self.mposkk = abs(self.mposkk)

                self.radd = self.myentryprice * (1 + self.mpr)
                self.sexit = self.myentryprice / (1 + self.mps)

            # 空头加仓
            if self.sig_shorta1:
                t_add += ',卖出'
                self.mposkk = -abs(self.mposkk)

                # self.radd = self.myentryprice * (1 - self.mpr)
                # self.sexit = self.myentryprice * (1 + self.mps)
                self.radd = self.myentryprice / (1 + self.mpr)
                self.sexit = self.myentryprice * (1 + self.mps)

            # 加仓日志
            if self.sig_longa1 or self.sig_shorta1:
                self.myorder = self.order_target(self.mposkk)  # 加仓中
                if self.myorder and hasattr(self.myorder, 'size'):
                    t_add += ',加仓中:{:d}'.format(self.myorder.size)
                else:
                    t_add += ',加仓中'
                t_add += ',持仓:{:}'.format(self.position.size)
                t_add += ',price:{:.2f}'.format(self.dtclose[0])
                t_add += ',总资产:{:.2f}'.format(assets)
                # self.log(t_add)

            # 离场 离场价格 SEXIT CLOSE
            if self.sig_longx1 or self.sig_shortx1:
                # 盈利或连续亏损时,减少下次开仓比率
                if self.turtleunits > 1:
                    self.mposkk = (self.mposkk / self.turtleunits)
                elif self.numlosst > 1:
                    self.mposkk = self.mposkk * (1 - self.mpposad)
                self.mposkk = self.mposkk if self.mposkk > self.mpposmin else self.mpposmin
                self.myexitprice = self.dtclose[0]
                self.positionflag = 0  # 清仓后头寸方向为0
                self.turtleunits = 0  # 加仓次数
                self.numlosst += 1  # 统计连续亏损次数
                self.buyorderthisbar = 1  # 标记该周期的交易状态
                self.mbstop = 0

            # 离场平仓
            if self.sig_longx1 or self.sig_shortx1:  # 平仓离场
                # 全部卖出
                self.myorder = self.close()
                t_exit += ',多头' if self.sig_longx1 else ',空头'
                t_exit += ',平仓中:{:}'.format(self.position.size)
                t_exit += ',price:{:.2f}'.format(self.dtclose[0])
                t_exit += ',总资产:{:.2f}'.format(assets)
                # self.log(t_exit)

    def stop(self):
        """测略结束时，多用于参数调优"""
        # self.log(' 参数 rpp:{:2d} '.format(self.p.rpp)
        #          + ' spp:{:2d} '.format(self.p.spp)
        #          + ' 期末资金: {:.2f} '.format(self.broker.getvalue())
        #          , doprint=True)


"""-------主函数---------"""
if __name__ == '__main__':
    runstrat()
