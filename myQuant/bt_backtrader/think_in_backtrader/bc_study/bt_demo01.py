# 免责声明：作者不保证本程序的正确性,也未经严格测试，不要据此进行实盘交易，一切后果自负

import backtrader as bt
from backtrader_ctpcn_api.ctpstore import CTPStore
from backtrader_ctpcn_api.ctputil import CtpStrategy
from time import sleep
import pandas as pd
import datetime
import pytz


#######################################################################
# 策略类
########################
class SmaCross(CtpStrategy):
    params = dict(
        smaperiod=2,
        store=None,
    )

    # 由ctpbee自动回调的事件方法
    def on_order(self, order) -> None:
        """ 报单回报 """
        # print('in strategy 报单回报on_order',order)

    def on_trade(self, trade) -> None:
        """ 成交回报 """
        # print('成交回报on_trade',trade, "\n")

    def on_position(self, position) -> None:
        """ 处理持仓回报 """
        # print('持仓回报on_position',position)

    def on_account(self, account) -> None:
        """ 处理账户信息回报 """
        # print('账户信息回报on_account',account)

    def on_contract(self, contract) -> None:
        """ 处理推送的合约信息 """

    #  print('合约信息回报on_account',contract)
    def on_tick(self, tick):
        pass

    def on_realtime(self):
        """
        1s触发一次的接口
        """

    # 以下为backtrader自己的事件方法
    def __init__(self):
        # ################
        #  与ctpbee挂钩
        ###################
        # 获取ctpbeeapi的引用
        self.beeapi = self.p.store.main_ctpbee_api
        # 把策略自己传给beeapi对象的属性strategy
        self.beeapi.set_strategy(self)
        self.beecenter = self.beeapi.app.center

        # d是否已进入实盘的标志
        self.live_data = {d: False for d in self.datas}

        # 移动均线
        move_average = {d: bt.ind.MovingAverageSimple(d, period=self.params.smaperiod) for d in self.datas}
        # 标的d的移动均线交叉信号指标
        self.crossover = {d: bt.ind.CrossOver(d, move_average[d]) for d in self.datas}

    def next(self):
        print('=========================================')
        print('in next')

        for d in self.datas:
            if not self.live_data[d]:
                return  # 不是实时数据（还处于历史数据回填中），不进入下单逻辑

        self.cancel_all()  # 撤销所有未成交订单

        for d in self.datas:
            print(d._name, d.datetime.datetime(0), 'o h l c ', d.open[0], d.high[0], d.low[0], d.close[0],
                  ' vol ', d.volume[0], 'openinterest', d.openinterest[0])

            # 标的持仓信息
            pos = self.beecenter.get_position(d._dataname)

            # 长仓数量
            long_pos = pos.long_volume if pos else 0
            # 短仓数量，为正数
            short_pos = pos.short_volume if pos else 0

            print(d._name, 'long pos', long_pos, 'short pos', short_pos)

            targetsize = 1  # 目标数量

            print(d._name, 'crossover', self.crossover[d][0])
            if self.crossover[d][0] == 1:  # 金叉
                print(d._name, '金叉， 要使净长仓达到目标数量', targetsize)
                olist = self.target_size(d.close[0], targetsize, d, buy_delta=5, sell_delta=5)
                print('olist', olist)
            elif self.crossover[d][0] == -1:  # 死叉
                print(d._name, '死叉， 要使净短仓达到目标数量', targetsize)
                # 注意目标size参数设为负数
                olist = self.target_size(d.close[0], - targetsize, d, buy_delta=5, sell_delta=5)
                print('olist', olist)

    def notify_data(self, data, status, *args, **kwargs):
        msg = f'数据状态: {data._getstatusname(status)}'
        print(data._name, msg)

        # 设置进入实盘标志
        if data._getstatusname(status) == 'LIVE':
            self.live_data[data] = True
            print()
            print('**********************************************')
            print(data._name, '进入实盘行情')
            print('**********************************************')

        else:
            self.live_data[data] = False

        #####策略结束##############################################


###########################################################
# 主程序开始
##################
if __name__ == '__main__':
    # http://122.51.136.165:50080/detail.html 查看行情服务器状态
    ctp_setting = {
        "CONNECT_INFO": {
            "userid": "????",  # 你在simnow注册的账户里的investorId
            "password": "????",  # 你在simnow注册的账户密码
            "brokerid": "9999",
            "md_address": "tcp://180.168.146.187:10211",  # 行情前置，行情服务器地址
            "td_address": "tcp://180.168.146.187:10201",  # 交易前置，交易服务器地址
            "product_info": "",
            "appid": "simnow_client_test",
            "auth_code": "0000000000000000"
        },
        "INTERFACE": "ctp",  # ctp/ctp_se载入接口名称，目前支持ctp生产以及ctp_se穿透式验证接口
        "TD_FUNC": True,  # 开启交易功能
        "MD_FUNC": True,  # 开启行情接收
        "XMIN": [],  # ctpbee生成几分钟bar，例如[1]
        "TODAY_EXCHANGE": ["SHFE", "INE"],  # 需要支持平今的交易所代码列表
        "CLOSE_PATTERN": "today",  # 对支持平今的交易所，指定优先平今或者平昨
    }
    tz = pytz.timezone('Asia/Shanghai')
    cerebro = bt.Cerebro()

    # 创建ctp store
    store = CTPStore(ctp_setting)

    # 定义数据
    # ag2206.SHFE是上期所白银期货  AP2210.ZCE郑商所 a2207.DCE大商所 中国金融期货交易所（IF2205.CFFEX）
    # vnpy 支持中国8大合规交易所中的5所，包括上海期货交易所，大连期货交易所、郑州期货交易所、中金所、能源所。
    data0_name = 'ag2206.SHFE'  # ag2206是上期所白银期货
    data1_name = 'ag2207.SHFE'

    # 回填数据文件所在路径
    csvpath = 'E:/myquant/backtrader_ctpcn/'
    data0 = store.getdata(dataname=data0_name, timeframe=bt.TimeFrame.Ticks,
                          # 回填数据来自哪里，如果不想回填，则设backfill_from=None
                          backfill_from=load_hist_ticks(csvpath + 'tickhistory.csv'),
                          qcheck=5,  # 等待远端tick的超时
                          sessionstart=datetime.time(21, 00, 00),  # 开市时间
                          sessionend=datetime.time(15, 00, 00),  # 闭市时间
                          tzinput=tz,
                          tz=tz
                          )

    # cerebro.adddata(data0)
    # 重采样tick合成需要的bar，注意设置name
    cerebro.resampledata(data0, timeframe=bt.TimeFrame.Seconds, compression=10, name=data0_name + '10s')

    # 多合约
    data1 = store.getdata(dataname=data1_name, timeframe=bt.TimeFrame.Ticks,
                          # 回填数据来自哪里，如果不想回填，则设backfill_from=None
                          backfill_from=load_hist_ticks(csvpath + 'tickhistory1.csv'),
                          qcheck=5,  # 等待远端tick的超时
                          sessionstart=datetime.time(21, 00, 00),  # 开市时间
                          sessionend=datetime.time(15, 00, 00),  # 闭市时间
                          tzinput=tz,
                          tz=tz
                          )
    # cerebro.adddata(data1)
    # 回放tick合成需要的bar，注意设置name
    cerebro.resampledata(data1, timeframe=bt.TimeFrame.Seconds, compression=10, name=data1_name + '10s')

    # 注入策略，注意store参数设置
    cerebro.addstrategy(SmaCross, store=store)

    # 当仿真行情与实盘同步时，is_realtime设为True，否则设为False
    cerebro.run(is_realtime=True, tz=tz)