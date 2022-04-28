#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys

from backtrader import Analyzer
from backtrader.utils import AutoOrderedDict, AutoDict
from backtrader.utils.py3 import MAXINT


class My_TradeAnalyzer(Analyzer):
    '''
    提供关闭交易的统计数据（还保留未平仓交易的数量）

      - Total Open/Closed Trades

      - Streak Won/Lost Current/Longest

      - ProfitAndLoss Total/Average

      - Won/Lost Count/ Total PNL/ Average PNL / Max PNL

      - Long/Short Count/ Total PNL / Average PNL / Max PNL

          - Won/Lost Count/ Total PNL/ Average PNL / Max PNL

      - Length (市场上的酒吧)

        - Total/Average/Max/Min

        - Won/Lost Total/Average/Max/Min

        - Long/Short Total/Average/Max/Min

          - Won/Lost Total/Average/Max/Min

    Note:

      分析器对字段使用“自动”字典，这意味着如果没有执行交易，则不会生成统计信息。

      在这种情况下，“get_analysis”返回的字典中将有一个字段子字段，即：

        - dictname['total']['total'] 的值为 0（该字段也可以使用点符号 dictname.total.total
    '''
    def create_analysis(self):
        self.rets = AutoOrderedDict()
        self.rets.total.total = 0

    def stop(self):
        super(My_TradeAnalyzer, self).stop()
        self.rets._close()

    def notify_trade(self, trade):
        if trade.justopened:
            # 交易刚刚开始
            self.rets.total.total += 1  # 总交易次数
            self.rets.total.open += 1  # 持仓头寸数

        elif trade.status == trade.Closed:  # 交易订单关闭
            trades = self.rets

            res = AutoDict()
            # 交易刚刚结束

            won = res.won = int(trade.pnlcomm >= 0.0)  # 是否盈利
            lost = res.lost = int(not won)  # 是否亏损
            tlong = res.tlong = trade.long  # 是否多头仓位
            tshort = res.tshort = not trade.long  # 是否空头仓位

            trades.total.open -= 1  # 持仓头寸数
            trades.total.closed += 1  # 平仓头寸数

            # Streak
            for wlname in ['won', 'lost']:
                wl = res[wlname]

                trades.streak[wlname].current *= wl
                trades.streak[wlname].current += wl

                ls = trades.streak[wlname].longest or 0
                trades.streak[wlname].longest = \
                    max(ls, trades.streak[wlname].current)

            trpnl = trades.pnl
            trpnl.gross.total += trade.pnl
            trpnl.gross.average = trades.pnl.gross.total / trades.total.closed
            trpnl.net.total += trade.pnlcomm
            trpnl.net.average = trades.pnl.net.total / trades.total.closed

            # Won/Lost statistics
            for wlname in ['won', 'lost']:
                wl = res[wlname]
                trwl = trades[wlname]

                trwl.total += wl  # won.total / lost.total

                trwlpnl = trwl.pnl
                pnlcomm = trade.pnlcomm * wl

                trwlpnl.total += pnlcomm
                trwlpnl.average = trwlpnl.total / (trwl.total or 1.0)

                wm = trwlpnl.max or 0.0
                func = max if wlname == 'won' else min
                trwlpnl.max = func(wm, pnlcomm)

            # Long/Short statistics
            for tname in ['long', 'short']:
                trls = trades[tname]
                ls = res['t' + tname]

                trls.total += ls  # long.total / short.total
                trls.pnl.total += trade.pnlcomm * ls
                trls.pnl.average = trls.pnl.total / (trls.total or 1.0)

                for wlname in ['won', 'lost']:
                    wl = res[wlname]
                    pnlcomm = trade.pnlcomm * wl * ls

                    trls[wlname] += wl * ls  # long.won / short.won

                    trls.pnl[wlname].total += pnlcomm
                    trls.pnl[wlname].average = \
                        trls.pnl[wlname].total / (trls[wlname] or 1.0)

                    wm = trls.pnl[wlname].max or 0.0
                    func = max if wlname == 'won' else min
                    trls.pnl[wlname].max = func(wm, pnlcomm)

            # Length
            trades.len.total += trade.barlen
            trades.len.average = trades.len.total / trades.total.closed
            ml = trades.len.max or 0
            trades.len.max = max(ml, trade.barlen)

            ml = trades.len.min or MAXINT
            trades.len.min = min(ml, trade.barlen)

            # Length Won/Lost
            for wlname in ['won', 'lost']:
                trwl = trades.len[wlname]
                wl = res[wlname]

                trwl.total += trade.barlen * wl
                trwl.average = trwl.total / (trades[wlname].total or 1.0)

                m = trwl.max or 0
                trwl.max = max(m, trade.barlen * wl)
                if trade.barlen * wl:
                    m = trwl.min or MAXINT
                    trwl.min = min(m, trade.barlen * wl)

            # Length Long/Short
            for lsname in ['long', 'short']:
                trls = trades.len[lsname]  # trades.len.long
                ls = res['t' + lsname]  # tlong/tshort

                barlen = trade.barlen * ls

                trls.total += barlen  # trades.len.long.total
                total_ls = trades[lsname].total   # trades.long.total
                trls.average = trls.total / (total_ls or 1.0)

                # max/min
                m = trls.max or 0
                trls.max = max(m, barlen)
                m = trls.min or MAXINT
                trls.min = min(m, barlen or m)

                for wlname in ['won', 'lost']:
                    wl = res[wlname]  # won/lost

                    barlen2 = trade.barlen * ls * wl

                    trls_wl = trls[wlname]  # trades.len.long.won
                    trls_wl.total += barlen2  # trades.len.long.won.total

                    trls_wl.average = \
                        trls_wl.total / (trades[lsname][wlname] or 1.0)

                    # max/min
                    m = trls_wl.max or 0
                    trls_wl.max = max(m, barlen2)
                    m = trls_wl.min or MAXINT
                    trls_wl.min = min(m, barlen2 or m)
