import json
import backtrader as bt

from ctpbeebt import CTPStore
from datetime import datetime, time


# Origin定义不要删除,ctpbee接口需要它
class Origin:
    """
    """

    def __init__(self, data):
        self.symbol = data._dataname.split('.')[0]
        self.exchange = data._name.split('.')[1]


# 说明在交易日上午8点45到下午3点，以及晚上8点45到凌晨2点45分，可进行实时行情模拟交易。
# 中国期货交易时段(日盘/夜盘)，只有在交易时段才能进行实时模拟仿真，其他时段只能进行非实时模拟仿真。双休日不能进行模拟仿真
DAY_START = time(8, 45)  # 日盘8点45开始
DAY_END = time(15, 0)  # 下午3点结束
NIGHT_START = time(20, 45)  # 夜盘晚上8点45开始
NIGHT_END = time(2, 45)  # 凌晨2点45结束


# 是否在交易时段
def is_trading_period():
    """
    """
    current_time = datetime.now().time()
    trading = False
    if ((current_time >= DAY_START and current_time <= DAY_END)
            or (current_time >= NIGHT_START)
            or (current_time <= NIGHT_END)):
        trading = True
    return trading


class SmaCross(bt.Strategy):
    lines = ('sma',)
    params = dict(
        smaperiod=5,
        store=None,
    )

    def __init__(self):
        self.beeapi = self.p.store.main_ctpbee_api
        self.buy_order = None
        self.live_data = False
        # self.move_average = bt.ind.MovingAverageSimple(self.data, period=self.params.smaperiod)

    def prenext(self):
        print('in prenext')
        for d in self.datas:
            print(d._name, d.datetime.datetime(0), 'o h l c ', d.open[0], d.high[0], d.low[0], d.close[0], ' vol ', d.volume[0])

    def next(self):
        print('------------------------------------------ next start')

        for d in self.datas:
            print('d._name', d._name, 'd._dataname', d._dataname, d.datetime.datetime(0), 'o h l c ', d.open[0], d.high[0], d.low[0], d.close[0], ' vol ', d.volume[0])
            pos = self.beeapi.app.center.get_position(d._dataname)
            print('position', pos)
            # 可以访问持仓、成交、订单等各种实盘信息，如何访问参考 http://docs.ctpbee.com/modules/rec.html
            trades = self.beeapi.app.center.trades
            print('trades', trades)
            account = self.beeapi.app.center.account
            print('account', account)

        if not self.live_data:  # 不是实时数据(还处于历史数据回填中),不进入下单逻辑
            return

        # 开多仓
        print('live buy')
        # self.open_long(self.data0.close[0] + 3, 1, self.data0)
        print('---------------------------------------------------')

    def notify_order(self, order):
        print('订单状态 %s' % order.getstatusname())

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = f'notify_data Data Status: {data._getstatusname(status)}'
        print(dt, dn, msg)
        if data._getstatusname(status) == 'LIVE':
            self.live_data = True
        else:
            self.live_data = False

    # 以下是下单函数
    def open_long(self, price, size, data):
        self.beeapi.action.buy(price, size, Origin(data))

    def open_short(self, price, size, data):
        self.beeapi.action.short(price, size, Origin(data))

    def close_long(self, price, size, data):
        self.beeapi.action.cover(price, size, Origin(data))

    def close_short(self, price, size, data):
        self.beeapi.action.sell(price, size, Origin(data))


# 主程序开始
if __name__ == '__main__':
    with open('./params-simnow.json', 'r', encoding='utf-8') as f:
        ctp_setting = json.load(f)

    cerebro = bt.Cerebro(live=True)

    store = CTPStore(ctp_setting, debug=True)
    cerebro.addstrategy(SmaCross, store=store)

    # 由于历史回填数据从akshare拿，最细1分钟bar，所以以下实盘也只接收1分钟bar
    # https://www.akshare.xyz/zh_CN/latest/data/futures/futures.html#id106

    data0 = store.getdata(dataname='c2209.DCE', timeframe=bt.TimeFrame.Minutes,  # 注意符号必须带交易所代码。ag2206.SHFE
                          num_init_backfill=2 if is_trading_period() else 0)  # 初始回填bar数，使用TEST服务器进行模拟实盘时，要设为0
    cerebro.adddata(data0)


    # data1 = store.getdata(dataname='rb2210.SHFE', timeframe=bt.TimeFrame.Minutes,  # 注意符号必须带交易所代码。rb2210.SHFE
    #                       num_init_backfill=10 if is_trading_period() else 0)  # 初始回填bar数，使用TEST服务器进行模拟实盘时，要设为0
    # cerebro.adddata(data1)


    cerebro.run()
