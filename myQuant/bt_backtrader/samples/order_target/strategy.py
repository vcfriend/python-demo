#!/usr/bin389/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
import copy
import datetime
import inspect
import itertools
import operator

from .utils.py3 import (filter, keys, integer_types, iteritems, itervalues,
                        map, MAXINT, string_types, with_metaclass)

import backtrader as bt
from .lineiterator import LineIterator, StrategyBase
from .lineroot import LineSingle
from .lineseries import LineSeriesStub
from .metabase import ItemCollection, findowner
from .trade import Trade
from .utils import OrderedDict, AutoOrderedDict, AutoDictList


class MetaStrategy(StrategyBase.__class__):
    _indcol = dict()

    def __new__(meta, name, bases, dct):
        # Hack to support original method name for notify_order
        if 'notify' in dct:
            # rename 'notify' to 'notify_order'
            dct['notify_order'] = dct.pop('notify')
        if 'notify_operation' in dct:
            # rename 'notify' to 'notify_order'
            dct['notify_trade'] = dct.pop('notify_operation')

        return super(MetaStrategy, meta).__new__(meta, name, bases, dct)

    def __init__(cls, name, bases, dct):
        '''
        Class has already been created ... register subclasses
        '''
        # Initialize the class
        super(MetaStrategy, cls).__init__(name, bases, dct)

        if not cls.aliased and \
                name != 'Strategy' and not name.startswith('_'):
            cls._indcol[name] = cls

    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = super(MetaStrategy, cls).donew(*args, **kwargs)

        # Find the owner and store it
        _obj.env = _obj.cerebro = cerebro = findowner(_obj, bt.Cerebro)
        _obj._id = cerebro._next_stid()

        return _obj, args, kwargs

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaStrategy, cls).dopreinit(_obj, *args, **kwargs)
        _obj.broker = _obj.env.broker
        _obj._sizer = bt.sizers.FixedSize()
        _obj._orders = list()
        _obj._orderspending = list()
        _obj._trades = collections.defaultdict(AutoDictList)
        _obj._tradespending = list()

        _obj.stats = _obj.observers = ItemCollection()
        _obj.analyzers = ItemCollection()
        _obj._alnames = collections.defaultdict(itertools.count)
        _obj.writers = list()

        _obj._slave_analyzers = list()

        _obj._tradehistoryon = False

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaStrategy, cls).dopostinit(_obj, *args, **kwargs)

        _obj._sizer.set(_obj, _obj.broker)

        return _obj, args, kwargs


class Strategy(with_metaclass(MetaStrategy, StrategyBase)):
    '''
    Base class to be subclassed for user defined strategies.
    '''

    _ltype = LineIterator.StratType

    csv = True
    _oldsync = False  # update clock using old methodology : data 0

    # keep the latest delivered data date in the line
    lines = ('datetime',)

    def qbuffer(self, savemem=0, replaying=False):
        '''Enable the memory saving schemes. Possible values for ``savemem``:

          0: No savings. Each lines object keeps in memory all values

          1: All lines objects save memory, using the strictly minimum needed

        Negative values are meant to be used when plotting is required:

          -1: Indicators at Strategy Level and Observers do not enable memory
              savings (but anything declared below it does)

          -2: Same as -1 plus activation of memory saving for any indicators
              which has declared *plotinfo.plot* as False (will not be plotted)
        '''
        if savemem < 0:
            # Get any attribute which labels itself as Indicator
            for ind in self._lineiterators[self.IndType]:
                subsave = isinstance(ind, (LineSingle,))
                if not subsave and savemem < -1:
                    subsave = not ind.plotinfo.plot
                ind.qbuffer(savemem=subsave)

        elif savemem > 0:
            for data in self.datas:
                data.qbuffer(replaying=replaying)

            for line in self.lines:
                line.qbuffer(savemem=1)

            # Save in all object types depending on the strategy
            for itcls in self._lineiterators:
                for it in self._lineiterators[itcls]:
                    it.qbuffer(savemem=1)

    def _periodset(self):
        dataids = [id(data) for data in self.datas]

        _dminperiods = collections.defaultdict(list)
        for lineiter in self._lineiterators[LineIterator.IndType]:
            # if multiple datas are used and multiple timeframes the larger
            # timeframe may place larger time constraints in calling next.
            clk = getattr(lineiter, '_clock', None)
            if clk is None:
                clk = getattr(lineiter._owner, '_clock', None)
                if clk is None:
                    continue

            while True:
                if id(clk) in dataids:
                    break  # already top-level clock (data feed)

                # See if the current clock has higher level clocks
                clk2 = getattr(clk, '_clock', None)
                if clk2 is None:
                    clk2 = getattr(clk._owner, '_clock', None)

                if clk2 is None:
                    break  # if no clock found, bail out

                clk = clk2  # keep the ref and try to go up the hierarchy

            if clk is None:
                continue  # no clock found, go to next

            # LineSeriesStup wraps a line and the clock is the wrapped line and
            # no the wrapper itself.
            if isinstance(clk, LineSeriesStub):
                clk = clk.lines[0]

            _dminperiods[clk].append(lineiter._minperiod)

        self._minperiods = list()
        for data in self.datas:

            # Do not only consider the data as clock but also its lines which
            # may have been individually passed as clock references and
            # discovered as clocks above

            # Initialize with data min period if any
            dlminperiods = _dminperiods[data]

            for l in data.lines:  # search each line for min periods
                if l in _dminperiods:
                    dlminperiods += _dminperiods[l]  # found, add it

            # keep the reference to the line if any was found
            _dminperiods[data] = [max(dlminperiods)] if dlminperiods else []

            dminperiod = max(_dminperiods[data] or [data._minperiod])
            self._minperiods.append(dminperiod)

        # Set the minperiod
        minperiods = \
            [x._minperiod for x in self._lineiterators[LineIterator.IndType]]
        self._minperiod = max(minperiods or [self._minperiod])

    def _addwriter(self, writer):
        '''
        Unlike the other _addxxx functions this one receives an instance
        because the writer works at cerebro level and is only passed to the
        strategy to simplify the logic
        '''
        self.writers.append(writer)

    def _addindicator(self, indcls, *indargs, **indkwargs):
        indcls(*indargs, **indkwargs)

    def _addanalyzer_slave(self, ancls, *anargs, **ankwargs):
        '''Like _addanalyzer but meant for observers (or other entities) which
        rely on the output of an analyzer for the data. These analyzers have
        not been added by the user and are kept separate from the main
        analyzers

        Returns the created analyzer
        '''
        analyzer = ancls(*anargs, **ankwargs)
        self._slave_analyzers.append(analyzer)
        return analyzer

    def _getanalyzer_slave(self, idx):
        return self._slave_analyzers.append[idx]

    def _addanalyzer(self, ancls, *anargs, **ankwargs):
        anname = ankwargs.pop('_name', '') or ancls.__name__.lower()
        nsuffix = next(self._alnames[anname])
        anname += str(nsuffix or '')  # 0 (first instance) gets no suffix
        analyzer = ancls(*anargs, **ankwargs)
        self.analyzers.append(analyzer, anname)

    def _addobserver(self, multi, obscls, *obsargs, **obskwargs):
        obsname = obskwargs.pop('obsname', '')
        if not obsname:
            obsname = obscls.__name__.lower()

        if not multi:
            newargs = list(itertools.chain(self.datas, obsargs))
            obs = obscls(*newargs, **obskwargs)
            self.stats.append(obs, obsname)
            return

        setattr(self.stats, obsname, list())
        l = getattr(self.stats, obsname)

        for data in self.datas:
            obs = obscls(data, *obsargs, **obskwargs)
            l.append(obs)

    def _getminperstatus(self):
        # check the min period status connected to datas
        dlens = map(operator.sub, self._minperiods, map(len, self.datas))
        self._minperstatus = minperstatus = max(dlens)
        return minperstatus

    def prenext_open(self):
        pass

    def nextstart_open(self):
        self.next_open()

    def next_open(self):
        pass

    def _oncepost_open(self):
        minperstatus = self._minperstatus
        if minperstatus < 0:
            self.next_open()
        elif minperstatus == 0:
            self.nextstart_open()  # only called for the 1st value
        else:
            self.prenext_open()

    def _oncepost(self, dt):
        for indicator in self._lineiterators[LineIterator.IndType]:
            if len(indicator._clock) > len(indicator):
                indicator.advance()

        if self._oldsync:
            # Strategy has not been reset, the line is there
            self.advance()
        else:
            # strategy has been reset to beginning. advance step by step
            self.forward()

        self.lines.datetime[0] = dt
        self._notify()

        minperstatus = self._getminperstatus()
        if minperstatus < 0:
            self.next()
        elif minperstatus == 0:
            self.nextstart()  # only called for the 1st value
        else:
            self.prenext()

        self._next_analyzers(minperstatus, once=True)
        self._next_observers(minperstatus, once=True)

        self.clear()

    def _clk_update(self):
        if self._oldsync:
            clk_len = super(Strategy, self)._clk_update()
            self.lines.datetime[0] = max(d.datetime[0]
                                         for d in self.datas if len(d))
            return clk_len

        newdlens = [len(d) for d in self.datas]
        if any(nl > l for l, nl in zip(self._dlens, newdlens)):
            self.forward()

        self.lines.datetime[0] = max(d.datetime[0]
                                     for d in self.datas if len(d))
        self._dlens = newdlens

        return len(self)

    def _next_open(self):
        minperstatus = self._minperstatus
        if minperstatus < 0:
            self.next_open()
        elif minperstatus == 0:
            self.nextstart_open()  # only called for the 1st value
        else:
            self.prenext_open()

    def _next(self):
        super(Strategy, self)._next()

        minperstatus = self._getminperstatus()
        self._next_analyzers(minperstatus)
        self._next_observers(minperstatus)

        self.clear()

    def _next_observers(self, minperstatus, once=False):
        for observer in self._lineiterators[LineIterator.ObsType]:
            for analyzer in observer._analyzers:
                if minperstatus < 0:
                    analyzer._next()
                elif minperstatus == 0:
                    analyzer._nextstart()  # only called for the 1st value
                else:
                    analyzer._prenext()

            if once:
                if len(self) > len(observer):
                    if self._oldsync:
                        observer.advance()
                    else:
                        observer.forward()

                if minperstatus < 0:
                    observer.next()
                elif minperstatus == 0:
                    observer.nextstart()  # only called for the 1st value
                elif len(observer):
                    observer.prenext()
            else:
                observer._next()

    def _next_analyzers(self, minperstatus, once=False):
        for analyzer in self.analyzers:
            if minperstatus < 0:
                analyzer._next()
            elif minperstatus == 0:
                analyzer._nextstart()  # only called for the 1st value
            else:
                analyzer._prenext()

    def _settz(self, tz):
        self.lines.datetime._settz(tz)

    def _start(self):
        self._periodset()

        for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
            analyzer._start()

        for obs in self.observers:
            if not isinstance(obs, list):
                obs = [obs]  # support of multi-data observers

            for o in obs:
                o._start()

        # change operators to stage 2
        self._stage2()

        self._dlens = [len(data) for data in self.datas]

        self._minperstatus = MAXINT  # start in prenext

        self.start()

    def start(self):
        '''Called right before the backtesting is about to be started.'''
        pass

    def getwriterheaders(self):
        self.indobscsv = [self]

        indobs = itertools.chain(
            self.getindicators_lines(), self.getobservers())
        self.indobscsv.extend(filter(lambda x: x.csv, indobs))

        headers = list()

        # prepare the indicators/observers data headers
        for iocsv in self.indobscsv:
            name = iocsv.plotinfo.plotname or iocsv.__class__.__name__
            headers.append(name)
            headers.append('len')
            headers.extend(iocsv.getlinealiases())

        return headers

    def getwritervalues(self):
        values = list()

        for iocsv in self.indobscsv:
            name = iocsv.plotinfo.plotname or iocsv.__class__.__name__
            values.append(name)
            lio = len(iocsv)
            values.append(lio)
            if lio:
                values.extend(map(lambda l: l[0], iocsv.lines.itersize()))
            else:
                values.extend([''] * iocsv.lines.size())

        return values

    def getwriterinfo(self):
        wrinfo = AutoOrderedDict()

        wrinfo['Params'] = self.p._getkwargs()

        sections = [
            ['Indicators', self.getindicators_lines()],
            ['Observers', self.getobservers()]
        ]

        for sectname, sectitems in sections:
            sinfo = wrinfo[sectname]
            for item in sectitems:
                itname = item.__class__.__name__
                sinfo[itname].Lines = item.lines.getlinealiases() or None
                sinfo[itname].Params = item.p._getkwargs() or None

        ainfo = wrinfo.Analyzers

        # Internal Value Analyzer
        ainfo.Value.Begin = self.broker.startingcash
        ainfo.Value.End = self.broker.getvalue()

        # no slave analyzers for writer
        for aname, analyzer in self.analyzers.getitems():
            ainfo[aname].Params = analyzer.p._getkwargs() or None
            ainfo[aname].Analysis = analyzer.get_analysis()

        return wrinfo

    def _stop(self):
        self.stop()

        for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
            analyzer._stop()

        # change operators back to stage 1 - allows reuse of datas
        self._stage1()

    def stop(self):
        '''Called right before the backtesting is about to be stopped'''
        pass

    def set_tradehistory(self, onoff=True):
        self._tradehistoryon = onoff

    def clear(self):
        self._orders.extend(self._orderspending)
        self._orderspending = list()
        self._tradespending = list()

    def _addnotification(self, order, quicknotify=False):
        if not order.p.simulated:
            self._orderspending.append(order)

        if quicknotify:
            qorders = [order]
            qtrades = []

        if not order.executed.size:
            if quicknotify:
                self._notify(qorders=qorders, qtrades=qtrades)
            return

        tradedata = order.data._compensate
        if tradedata is None:
            tradedata = order.data

        datatrades = self._trades[tradedata][order.tradeid]
        if not datatrades:
            trade = Trade(data=tradedata, tradeid=order.tradeid,
                          historyon=self._tradehistoryon)
            datatrades.append(trade)
        else:
            trade = datatrades[-1]

        for exbit in order.executed.iterpending():
            if exbit is None:
                break

            if exbit.closed:
                trade.update(order,
                             exbit.closed,
                             exbit.price,
                             exbit.closedvalue,
                             exbit.closedcomm,
                             exbit.pnl,
                             comminfo=order.comminfo)

                if trade.isclosed:
                    self._tradespending.append(copy.copy(trade))
                    if quicknotify:
                        qtrades.append(copy.copy(trade))

            # Update it if needed
            if exbit.opened:
                if trade.isclosed:
                    trade = Trade(data=tradedata, tradeid=order.tradeid,
                                  historyon=self._tradehistoryon)
                    datatrades.append(trade)

                trade.update(order,
                             exbit.opened,
                             exbit.price,
                             exbit.openedvalue,
                             exbit.openedcomm,
                             exbit.pnl,
                             comminfo=order.comminfo)

                # This extra check covers the case in which different tradeid
                # orders have put the position down to 0 and the next order
                # "opens" a position but "closes" the trade
                if trade.isclosed:
                    self._tradespending.append(copy.copy(trade))
                    if quicknotify:
                        qtrades.append(copy.copy(trade))

            if trade.justopened:
                self._tradespending.append(copy.copy(trade))
                if quicknotify:
                    qtrades.append(copy.copy(trade))

        if quicknotify:
            self._notify(qorders=qorders, qtrades=qtrades)

    def _notify(self, qorders=[], qtrades=[]):
        if self.cerebro.p.quicknotify:
            # need to know if quicknotify is on, to not reprocess pendingorders
            # and pendingtrades, which have to exist for things like observers
            # which look into it
            procorders = qorders
            proctrades = qtrades
        else:
            procorders = self._orderspending
            proctrades = self._tradespending

        for order in procorders:
            if order.exectype != order.Historical or order.histnotify:
                self.notify_order(order)
            for analyzer in itertools.chain(self.analyzers,
                                            self._slave_analyzers):
                analyzer._notify_order(order)

        for trade in proctrades:
            self.notify_trade(trade)
            for analyzer in itertools.chain(self.analyzers,
                                            self._slave_analyzers):
                analyzer._notify_trade(trade)

        if qorders:
            return  # cash is notified on a regular basis

        cash = self.broker.getcash()
        value = self.broker.getvalue()
        fundvalue = self.broker.fundvalue
        fundshares = self.broker.fundshares

        self.notify_cashvalue(cash, value)
        self.notify_fund(cash, value, fundvalue, fundshares)
        for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
            analyzer._notify_cashvalue(cash, value)
            analyzer._notify_fund(cash, value, fundvalue, fundshares)

    def add_timer(self, when,
                  offset=datetime.timedelta(), repeat=datetime.timedelta(),
                  weekdays=[], weekcarry=False,
                  monthdays=[], monthcarry=True,
                  allow=None,
                  tzdata=None, cheat=False,
                  *args, **kwargs):
        '''
        **Note**: can be called during ``__init__`` or ``start``

        Schedules a timer to invoke either a specified callback or the
        ``notify_timer`` of one or more strategies.

        Arguments:

          - ``when``: can be

            - ``datetime.time`` instance (see below ``tzdata``)
            - ``bt.timer.SESSION_START`` to reference a session start
            - ``bt.timer.SESSION_END`` to reference a session end

         - ``offset`` which must be a ``datetime.timedelta`` instance

           Used to offset the value ``when``. It has a meaningful use in
           combination with ``SESSION_START`` and ``SESSION_END``, to indicated
           things like a timer being called ``15 minutes`` after the session
           start.

          - ``repeat`` which must be a ``datetime.timedelta`` instance

            Indicates if after a 1st call, further calls will be scheduled
            within the same session at the scheduled ``repeat`` delta

            Once the timer goes over the end of the session it is reset to the
            original value for ``when``

          - ``weekdays``: a **sorted** iterable with integers indicating on
            which days (iso codes, Monday is 1, Sunday is 7) the timers can
            be actually invoked

            If not specified, the timer will be active on all days

          - ``weekcarry`` (default: ``False``). If ``True`` and the weekday was
            not seen (ex: trading holiday), the timer will be executed on the
            next day (even if in a new week)

          - ``monthdays``: a **sorted** iterable with integers indicating on
            which days of the month a timer has to be executed. For example
            always on day *15* of the month

            If not specified, the timer will be active on all days

          - ``monthcarry`` (default: ``True``). If the day was not seen
            (weekend, trading holiday), the timer will be executed on the next
            available day.

          - ``allow`` (default: ``None``). A callback which receives a
            `datetime.date`` instance and returns ``True`` if the date is
            allowed for timers or else returns ``False``

          - ``tzdata`` which can be either ``None`` (default), a ``pytz``
            instance or a ``data feed`` instance.

            ``None``: ``when`` is interpreted at face value (which translates
            to handling it as if it where UTC even if it's not)

            ``pytz`` instance: ``when`` will be interpreted as being specified
            in the local time specified by the timezone instance.

            ``data feed`` instance: ``when`` will be interpreted as being
            specified in the local time specified by the ``tz`` parameter of
            the data feed instance.

            **Note**: If ``when`` is either ``SESSION_START`` or
              ``SESSION_END`` and ``tzdata`` is ``None``, the 1st *data feed*
              in the system (aka ``self.data0``) will be used as the reference
              to find out the session times.

          - ``cheat`` (default ``False``) if ``True`` the timer will be called
            before the broker has a chance to evaluate the orders. This opens
            the chance to issue orders based on opening price for example right
            before the session starts

          - ``*args``: any extra args will be passed to ``notify_timer``

          - ``**kwargs``: any extra kwargs will be passed to ``notify_timer``

        Return Value:

          - The created timer

        '''
        return self.cerebro._add_timer(
            owner=self, when=when, offset=offset, repeat=repeat,
            weekdays=weekdays, weekcarry=weekcarry,
            monthdays=monthdays, monthcarry=monthcarry,
            allow=allow,
            tzdata=tzdata, strats=False, cheat=cheat,
            *args, **kwargs)

    def notify_timer(self, timer, when, *args, **kwargs):
        '''接收定时器通知，其中``timer`` 是``add_timer`` 返回的定时器，``when`` 是调用时间。
        ``args`` 和 ``kwargs`` 是传递给``add_timer`` 的任何附加参数

        实际的 ``when`` 时间可以晚一些，但系统之前可能无法调用定时器。该值是定时器值，不是系统时间。
        '''
        pass

    def notify_cashvalue(self, cash, value):
        '''
        接收当前基金价值，策略经纪商的价值状态
        '''
        pass

    def notify_fund(self, cash, value, fundvalue, shares):
        '''
        收到当前现金、价值、基金价值和基金份额
        '''
        pass

    def notify_order(self, order):
        '''每当有一个变化时收到一个订单'''
        pass

    def notify_trade(self, trade):
        '''每当有变化时接收交易'''
        pass

    def notify_store(self, msg, *args, **kwargs):
        '''Receives a notification from a store provider'''
        pass

    def notify_data(self, data, status, *args, **kwargs):
        '''Receives a notification from data'''
        pass

    def getdatanames(self):
        '''
        返回现有数据名称的列表
        '''
        return keys(self.env.datasbyname)

    def getdatabyname(self, name):
        '''
        Returns a given data by name using the environment (cerebro)
        '''
        return self.env.datasbyname[name]

    def cancel(self, order):
        '''Cancels the order in the broker'''
        self.broker.cancel(order)

    def buy(self, data=None,
            size=None, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            parent=None, transmit=True,
            **kwargs):
        '''创建买入（多头）订单并将其发送给经纪人

          - ``data`` (default: ``None``)

            必须为哪些数据创建订单。如果“无”，那么系统中的第一个数据，
            “self.datas[0] 或 self.data0”（又名“self.data”）将被使用

          - ``size`` (default: ``None``)

            用于订单的数据单位的大小（正）。如果“无”，则通过“getsizer”检索的“sizer”实例将用于确定大小。

          - ``price`` (default: ``None``)

            使用价格（如果实际格式不符合最小报价大小要求，实时经纪人可能会对实际格式施加限制）

            ``None`` 对 ``Market`` 和 ``Close`` 订单有效（市场决定价格）

            对于 ``Limit``、``Stop`` 和 ``Stop Limit`` 订单，
            这个值决定触发点（在 ``Limit`` 的情况下，触发器显然是订单应该匹配的价格）

          - ``plimit``（默认：``None``）仅适用于``StopLimit``订单。

            这是设置隐含限价单的价格，一旦触发了止损（已使用“价格”）


          - ``trailamount``（默认值：``None``）

            如果订单类型是 StopTrail 或 StopTrailLimit，这是一个绝对数量，
            它决定了与价格的距离（低于卖出订单，高于买入订单）到保持追踪止损

          - ``trailpercent`` (default: ``None``)

            如果订单类型是 StopTrail 或 StopTrailLimit，这是一个百分比量，
            它确定与价格的距离（低于卖出订单，高于买入订单）以保持追踪止损（如果还指定了 ``trailamount`` 它将会被使用）

          - ``exectype`` (default: ``None``)

            可能的值：

            - ``Order.Market`` 或 ``None``。市价单将以下一个可用价格执行。在回测中，它将是下一个柱的开盘价

            - ``Order.Limit``. 只能以给定的“价格”或更好的价格执行的订单

            - ``Order.Stop``. 以“价格”触发并像“Order.Market”订单一样执行的订单

            - ``Order.StopLimit``. 以“价格”触发并作为隐式限价订单执行的订单，价格由“价格限制”给出

            - ``Order.Close``. 只能以时段收盘价执行的订单（通常在收盘竞价期间）

            - ``Order.StopTrail``. 以 ``price`` 减去 ``trailamount``（或 ``trailpercent``）触发的订单，如果价格远离止损则更新

            - ``Order.StopTrailLimit``. 以 ``price`` 减去 ``trailamount``（或 ``trailpercent``）触发的订单，如果价格远离止损则更新

          - ``valid`` (default: ``None``)

            可能的值：

              - ``None``:
              这会生成一个不会过期的订单（也就是取消前有效）并保留在市场中直到匹配或取消。
              实际上，经纪人倾向于施加时间限制，但这通常在时间上很遥远，以至于认为它不会过期

              - ``datetime.datetime`` or ``datetime.date`` instance:
              该日期将用于生成在给定日期时间之前有效的订单（也就是截止日期）

              - ``Order.DAY`` or ``0`` or ``timedelta()``:
              将生成在会话结束之前有效的一天（又名日订单）

              - ``numeric value``:
              这被假定为与“matplotlib”编码中的日期时间相对应的值（“backtrader”使用的那个），
              并将用于生成在该时间之前有效的订单（截至日期有效）

          - ``tradeid`` (default: ``0``)

            这是“backtrader”应用的一个内部值，用于跟踪同一资产的重叠交易。当通知订单状态的变化时，这个“tradeid”被发送回策略。

          - ``oco`` (default: ``None``)

            另一个“订单”实例。此订单将成为 OCO（订单取消其他）组的一部分。执行其中一个订单，立即取消同一组中的所有其他订单

          - ``parent`` (default: ``None``)

            控制一组订单之间的关系，例如由高端限价卖出和低端止损卖出包围的买入。
            在父订单被执行（它们变得活跃）或被取消到期（子订单也被取消）之前，高低端订单保持非活动状态，括号订单具有相同的大小

          - ``transmit`` (default: ``True``)

            指示是否必须传输订单，即：不仅放置在经纪人中，而且还发出。
            这意味着例如控制括号顺序，其中禁用父级和第一组子级的传输并为最后一个子级激活它，这会触发所有括号顺序的完全放置。

          - ``**kwargs``: 额外的代理实现可能支持额外的参数。 ``backtrader`` 会将 kwargs 传递给创建的订单对象

            示例：如果 ``backtrader`` 直接支持的 4 种订单执行类型还不够，
            例如在 Interactive Brokers 的情况下，可以将以下内容作为 kwargs 传递::

              orderType='LIT', lmtPrice=10.0, auxPrice=9.8

            这将覆盖 ``backtrader`` 创建的设置并生成 ``LIMIT IF TOUCHED`` 订单，其触及价格为 9.8，限价为 10.0。

        Returns:
          - 提交的订单

        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)

        data = data if data is not None else self.datas[0]
        size = size if size is not None else self.getsizing(data, isbuy=True)

        if size:
            return self.broker.buy(
                self, data,
                size=abs(size), price=price, plimit=plimit,
                exectype=exectype, valid=valid, tradeid=tradeid, oco=oco,
                trailamount=trailamount, trailpercent=trailpercent,
                parent=parent, transmit=transmit,
                **kwargs)

        return None

    def sell(self, data=None,
             size=None, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             parent=None, transmit=True,
             **kwargs):
        '''
        创建卖出（空头）订单并将其发送给经纪人 参见“买入”的文档以了解参数的说明 返回：提交的订单
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)

        data = data if data is not None else self.datas[0]
        size = size if size is not None else self.getsizing(data, isbuy=False)

        if size:
            return self.broker.sell(
                self, data,
                size=abs(size), price=price, plimit=plimit,
                exectype=exectype, valid=valid, tradeid=tradeid, oco=oco,
                trailamount=trailamount, trailpercent=trailpercent,
                parent=parent, transmit=transmit,
                **kwargs)

        return None

    def close(self, data=None, size=None, **kwargs):
        '''
        反对一个long/short头寸关闭它请参阅``buy``的文档以获取参数说明

        Note:

          - ``size``：如果调用者未提供（默认值：``None``），则从现有位置自动计算

        返回：提交的订单
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        size = abs(size if size is not None else possize)

        if possize > 0:
            return self.sell(data=data, size=size, **kwargs)
        elif possize < 0:
            return self.buy(data=data, size=size, **kwargs)

        return None

    def buy_bracket(self, data=None, size=None, price=None, plimit=None,
                    exectype=bt.Order.Limit, valid=None, tradeid=0,
                    trailamount=None, trailpercent=None, oargs={},
                    stopprice=None, stopexec=bt.Order.Stop, stopargs={},
                    limitprice=None, limitexec=bt.Order.Limit, limitargs={},
                    **kwargs):
        '''
        创建一个括号定单组(low side - buy order - high side)。默认行为如下：

          - Issue a **buy** order with execution ``Limit``

          - Issue a *low side* bracket **sell** order with execution ``Stop``

          - Issue a *high side* bracket **sell** order with execution
            ``Limit``.

        请参阅下面的不同参数

          - ``data`` (default: ``None``)

            必须为哪些数据创建订单。如果“无”，那么系统中的第一个数据，“self.datas[0] 或 self.data0”（又名“self.data”）将被使用

          - ``size`` (default: ``None``)

            用于订单的数据单位的大小（正）。

            如果“无”，则通过“getsizer”检索的“sizer”实例将用于确定大小。

            **Note**: The same size is applied to all 3 orders of the bracket

          - ``price`` (default: ``None``)

            Price to use (live brokers may place restrictions on the actual
            format if it does not comply to minimum tick size requirements)

            ``None`` is valid for ``Market`` and ``Close`` orders (the market
            determines the price)

            For ``Limit``, ``Stop`` and ``StopLimit`` orders this value
            determines the trigger point (in the case of ``Limit`` the trigger
            is obviously at which price the order should be matched)

          - ``plimit`` (default: ``None``)

            Only applicable to ``StopLimit`` orders. This is the price at which
            to set the implicit *Limit* order, once the *Stop* has been
            triggered (for which ``price`` has been used)

          - ``trailamount`` (default: ``None``)

            If the order type is StopTrail or StopTrailLimit, this is an
            absolute amount which determines the distance to the price (below
            for a Sell order and above for a buy order) to keep the trailing
            stop

          - ``trailpercent`` (default: ``None``)

            If the order type is StopTrail or StopTrailLimit, this is a
            percentage amount which determines the distance to the price (below
            for a Sell order and above for a buy order) to keep the trailing
            stop (if ``trailamount`` is also specified it will be used)

          - ``exectype`` (default: ``bt.Order.Limit``)

            Possible values: (see the documentation for the method ``buy``

          - ``valid`` (default: ``None``)

            Possible values: (see the documentation for the method ``buy``

          - ``tradeid`` (default: ``0``)

            Possible values: (see the documentation for the method ``buy``

          - ``oargs`` (default: ``{}``)

            Specific keyword arguments (in a ``dict``) to pass to the main side
            order. Arguments from the default ``**kwargs`` will be applied on
            top of this.

          - ``**kwargs``: additional broker implementations may support extra
            parameters. ``backtrader`` will pass the *kwargs* down to the
            created order objects

            Possible values: (see the documentation for the method ``buy``

            **Note**: this ``kwargs`` will be applied to the 3 orders of a
            bracket. See below for specific keyword arguments for the low and
            high side orders

          - ``stopprice`` (default: ``None``)

            Specific price for the *low side* stop order

          - ``stopexec`` (default: ``bt.Order.Stop``)

            Specific execution type for the *low side* order

          - ``stopargs`` (default: ``{}``)

            Specific keyword arguments (in a ``dict``) to pass to the low side
            order. Arguments from the default ``**kwargs`` will be applied on
            top of this.

          - ``limitprice`` (default: ``None``)

            Specific price for the *high side* stop order

          - ``stopexec`` (default: ``bt.Order.Limit``)

            Specific execution type for the *high side* order

          - ``limitargs`` (default: ``{}``)

            Specific keyword arguments (in a ``dict``) to pass to the high side
            order. Arguments from the default ``**kwargs`` will be applied on
            top of this.

        High/Low Side orders can be suppressed by using:

          - ``limitexec=None`` to suppress the *high side*

          - ``stopexec=None`` to suppress the *low side*

        Returns:

          - A list containing the 3 orders [order, stop side, limit side]

          - If high/low orders have been suppressed the return value will still
            contain 3 orders, but those suppressed will have a value of
            ``None``
        '''

        kargs = dict(size=size,
                     data=data, price=price, plimit=plimit, exectype=exectype,
                     valid=valid, tradeid=tradeid,
                     trailamount=trailamount, trailpercent=trailpercent)
        kargs.update(oargs)
        kargs.update(kwargs)
        kargs['transmit'] = limitexec is None and stopexec is None
        o = self.buy(**kargs)

        if stopexec is not None:
            # low side / stop
            kargs = dict(data=data, price=stopprice, exectype=stopexec,
                         valid=valid, tradeid=tradeid)
            kargs.update(stopargs)
            kargs.update(kwargs)
            kargs['parent'] = o
            kargs['transmit'] = limitexec is None
            kargs['size'] = o.size
            ostop = self.sell(**kargs)
        else:
            ostop = None

        if limitexec is not None:
            # high side / limit
            kargs = dict(data=data, price=limitprice, exectype=limitexec,
                         valid=valid, tradeid=tradeid)
            kargs.update(limitargs)
            kargs.update(kwargs)
            kargs['parent'] = o
            kargs['transmit'] = True
            kargs['size'] = o.size
            olimit = self.sell(**kargs)
        else:
            olimit = None

        return [o, ostop, olimit]

    def sell_bracket(self, data=None,
                     size=None, price=None, plimit=None,
                     exectype=bt.Order.Limit, valid=None, tradeid=0,
                     trailamount=None, trailpercent=None,
                     oargs={},
                     stopprice=None, stopexec=bt.Order.Stop, stopargs={},
                     limitprice=None, limitexec=bt.Order.Limit, limitargs={},
                     **kwargs):
        '''
        创建一个括号定单组（低端 - 买入定单 - 高端）。默认行为如下：

          - Issue a **sell** order with execution ``Limit``

          - Issue a *high side* bracket **buy** order with execution ``Stop``

          - Issue a *low side* bracket **buy** order with execution ``Limit``.

        See ``bracket_buy`` for the meaning of the parameters

        High/Low Side orders can be suppressed by using:

          - ``stopexec=None`` to suppress the *high side*

          - ``limitexec=None`` to suppress the *low side*

        Returns:

          - A list containing the 3 orders [order, stop side, limit side]

          - If high/low orders have been suppressed the return value will still
            contain 3 orders, but those suppressed will have a value of
            ``None``
        '''

        kargs = dict(size=size,
                     data=data, price=price, plimit=plimit, exectype=exectype,
                     valid=valid, tradeid=tradeid,
                     trailamount=trailamount, trailpercent=trailpercent)
        kargs.update(oargs)
        kargs.update(kwargs)
        kargs['transmit'] = limitexec is None and stopexec is None
        o = self.sell(**kargs)

        if stopexec is not None:
            # high side / stop
            kargs = dict(data=data, price=stopprice, exectype=stopexec,
                         valid=valid, tradeid=tradeid)
            kargs.update(stopargs)
            kargs.update(kwargs)
            kargs['parent'] = o
            kargs['transmit'] = limitexec is None  # transmit if last
            kargs['size'] = o.size
            ostop = self.buy(**kargs)
        else:
            ostop = None

        if limitexec is not None:
            # low side / limit
            kargs = dict(data=data, price=limitprice, exectype=limitexec,
                         valid=valid, tradeid=tradeid)
            kargs.update(limitargs)
            kargs.update(kwargs)
            kargs['parent'] = o
            kargs['transmit'] = True
            kargs['size'] = o.size
            olimit = self.buy(**kargs)
        else:
            olimit = None

        return [o, ostop, olimit]

    def order_target_size(self, data=None, target=0, **kwargs):
        '''
        Place an order to rebalance a position to have final size of ``target``

        The current ``position`` size is taken into account as the start point
        to achieve ``target``

          - If ``target`` > ``pos.size`` -> buy ``target - pos.size``

          - If ``target`` < ``pos.size`` -> sell ``pos.size - target``

        It returns either:

          - The generated order

          or

          - ``None`` if no order has been issued (``target == position.size``)
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        if not target and possize:
            return self.close(data=data, size=possize, **kwargs)

        elif target > possize:
            return self.buy(data=data, size=target - possize, **kwargs)

        elif target < possize:
            return self.sell(data=data, size=possize - target, **kwargs)

        return None  # no execution target == possize

    def order_target_value(self, data=None, target=0.0, price=None, **kwargs):
        '''
        下订单以重新平衡头寸，使其最终值为“目标”

        将当前的“值”作为实现“目标”的起点

          - If no ``target`` then close postion on data
          - If ``target`` > ``value`` then buy on data
          - If ``target`` < ``value`` then sell on data

        It returns either:

          - 生成的订单

          or

          - ``无``如果没有发出命令
        '''

        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        if not target and possize:  # closing a position
            return self.close(data=data, size=possize, price=price, **kwargs)

        else:
            value = self.broker.getvalue(datas=[data])  # 保证金占用
            comminfo = self.broker.getcommissioninfo(data)

            # Make sure a price is there
            price = price if price is not None else data.close[0]

            if target > 0:
                cash = abs(abs(target) - value)
                cash = cash if cash < (self.broker.getcash()) else self.broker.getcash()  # 避免开仓保证金不足
                # cash = (cash - comminfo.get_margin(price)) if (cash // comminfo.get_margin(price) > 1) else cash
                size = comminfo.getsize(price, cash)
                return self.buy(data=data, size=size, price=price, **kwargs)

            elif target < 0:
                # cash = abs(value - abs(target))
                cash = abs(value - abs(target)) if abs(target) < value else abs(abs(target) - value)  #金字塔开仓模式
                cash = cash if cash < (self.broker.getcash()) else self.broker.getcash()  # 避免开仓保证金不足
                # cash = (cash - comminfo.get_margin(price)) if (cash // comminfo.get_margin(price) > 1) else cash
                size = comminfo.getsize(price, cash)
                return self.sell(data=data, size=size, price=price, **kwargs)

        return None  # no execution size == possize

    def order_target_percent(self, data=None, target=0.0, **kwargs):
        '''
        下订单以重新平衡头寸，使其最终价值达到当前投资组合“价值”的“目标”百分比

        ``target`` 用十进制表示：``0.05`` -> ``5%``

        它使用 ``order_target_value`` 来执行订单。

        Example:
          - ``target=0.05`` 并且投资组合价值是 ``100``

          - The ``value`` 要达到的是 ``0.05 * 100 = 5``

          - ``5`` 作为``target`` 值传递给``order_target_value``

        将当前的“值”作为实现“目标”的起点

        ``position.size`` 用于确定仓位是否为 ``long`` ``short``

          - If ``target`` > ``value``
            - buy if ``pos.size >= 0`` (增加多头头寸)
            - sell if ``pos.size < 0`` (增加空头头寸)

          - If ``target`` < ``value``
            - sell if ``pos.size >= 0`` (减少多头头寸)
            - buy if ``pos.size < 0`` (减少空头头寸)

        它返回：

          - 生成的订单

          or

          - ``None`` 如果没有发出订单（``target == position.size``）
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        target *= self.broker.getvalue()

        return self.order_target_value(data=data, target=target, **kwargs)

    def getposition(self, data=None, broker=None):
        '''
        返回给定代理中给定数据的当前位置。

        如果两者都为无，则将使用主要数据和默认代理一个属性“位置”也可用
        '''
        data = data if data is not None else self.datas[0]
        broker = broker or self.broker
        return broker.getposition(data)

    position = property(getposition)

    def getpositionbyname(self, name=None, broker=None):
        '''
        返回给定代理中给定名称的当前位置。

        如果两者都是None，则将使用主要数据和默认代理一个属性“positionbyname”也可用
        '''
        data = self.datas[0] if not name else self.getdatabyname(name)
        broker = broker or self.broker
        return broker.getposition(data)

    positionbyname = property(getpositionbyname)

    def getpositions(self, broker=None):
        '''
        Returns the current by data positions directly from the broker

        If the given ``broker`` is None, the default broker will be used

        A property ``positions`` is also available
        '''
        broker = broker or self.broker
        return broker.positions

    positions = property(getpositions)

    def getpositionsbyname(self, broker=None):
        '''
        Returns the current by name positions directly from the broker

        If the given ``broker`` is None, the default broker will be used

        A property ``positionsbyname`` is also available
        '''
        broker = broker or self.broker
        positions = broker.positions

        posbyname = collections.OrderedDict()
        for name, data in iteritems(self.env.datasbyname):
            posbyname[name] = positions[data]

        return posbyname

    positionsbyname = property(getpositionsbyname)

    def _addsizer(self, sizer, *args, **kwargs):
        if sizer is None:
            self.setsizer(bt.sizers.FixedSize())
        else:
            self.setsizer(sizer(*args, **kwargs))

    def setsizer(self, sizer):
        '''
        Replace the default (fixed stake) sizer
        '''
        self._sizer = sizer
        sizer.set(self, self.broker)
        return sizer

    def getsizer(self):
        '''
        Returns the sizer which is in used if automatic statke calculation is
        used

        Also available as ``sizer``
        '''
        return self._sizer

    sizer = property(getsizer, setsizer)

    def getsizing(self, data=None, isbuy=True):
        '''
        Return the stake calculated by the sizer instance for the current
        situation
        '''
        data = data if data is not None else self.datas[0]
        return self._sizer.getsizing(data, isbuy=isbuy)


class MetaSigStrategy(Strategy.__class__):

    def __new__(meta, name, bases, dct):
        # map user defined next to custom to be able to call own method before
        if 'next' in dct:
            dct['_next_custom'] = dct.pop('next')

        cls = super(MetaSigStrategy, meta).__new__(meta, name, bases, dct)

        # after class creation remap _next_catch to be next
        cls.next = cls._next_catch
        return cls

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaSigStrategy, cls).dopreinit(_obj, *args, **kwargs)

        _obj._signals = collections.defaultdict(list)

        _data = _obj.p._data
        if _data is None:
            _obj._dtarget = _obj.data0
        elif isinstance(_data, integer_types):
            _obj._dtarget = _obj.datas[_data]
        elif isinstance(_data, string_types):
            _obj._dtarget = _obj.getdatabyname(_data)
        elif isinstance(_data, bt.LineRoot):
            _obj._dtarget = _data
        else:
            _obj._dtarget = _obj.data0

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaSigStrategy, cls).dopostinit(_obj, *args, **kwargs)

        for sigtype, sigcls, sigargs, sigkwargs in _obj.p.signals:
            _obj._signals[sigtype].append(sigcls(*sigargs, **sigkwargs))

        # Record types of signals
        _obj._longshort = bool(_obj._signals[bt.SIGNAL_LONGSHORT])

        _obj._long = bool(_obj._signals[bt.SIGNAL_LONG])
        _obj._short = bool(_obj._signals[bt.SIGNAL_SHORT])

        _obj._longexit = bool(_obj._signals[bt.SIGNAL_LONGEXIT])
        _obj._shortexit = bool(_obj._signals[bt.SIGNAL_SHORTEXIT])

        return _obj, args, kwargs


class SignalStrategy(with_metaclass(MetaSigStrategy, Strategy)):
    '''This subclass of ``Strategy`` is meant to to auto-operate using
    **signals**.

    *Signals* are usually indicators and the expected output values:

      - ``> 0`` is a ``long`` indication

      - ``< 0`` is a ``short`` indication

    There are 5 types of *Signals*, broken in 2 groups.

    **Main Group**:

      - ``LONGSHORT``: both ``long`` and ``short`` indications from this signal
        are taken

      - ``LONG``:
        - ``long`` indications are taken to go long
        - ``short`` indications are taken to *close* the long position. But:

          - If a ``LONGEXIT`` (see below) signal is in the system it will be
            used to exit the long

          - If a ``SHORT`` signal is available and no ``LONGEXIT`` is available
            , it will be used to close a ``long`` before opening a ``short``

      - ``SHORT``:
        - ``short`` indications are taken to go short
        - ``long`` indications are taken to *close* the short position. But:

          - If a ``SHORTEXIT`` (see below) signal is in the system it will be
            used to exit the short

          - If a ``LONG`` signal is available and no ``SHORTEXIT`` is available
            , it will be used to close a ``short`` before opening a ``long``

    **Exit Group**:

      This 2 signals are meant to override others and provide criteria for
      exitins a ``long``/``short`` position

      - ``LONGEXIT``: ``short`` indications are taken to exit ``long``
        positions

      - ``SHORTEXIT``: ``long`` indications are taken to exit ``short``
        positions

    **Order Issuing**

      Orders execution type is ``Market`` and validity is ``None`` (*Good until
      Canceled*)

    Params:

      - ``signals`` (default: ``[]``): a list/tuple of lists/tuples that allows
        the instantiation of the signals and allocation to the right type

        This parameter is expected to be managed through ``cerebro.add_signal``

      - ``_accumulate`` (default: ``False``): allow to enter the market
        (long/short) even if already in the market

      - ``_concurrent`` (default: ``False``): allow orders to be issued even if
        orders are already pending execution

      - ``_data`` (default: ``None``): if multiple datas are present in the
        system which is the target for orders. This can be

        - ``None``: The first data in the system will be used

        - An ``int``: indicating the data that was inserted at that position

        - An ``str``: name given to the data when creating it (parameter
          ``name``) or when adding it cerebro with ``cerebro.adddata(...,
          name=)``

        - A ``data`` instance

    '''

    params = (
        ('signals', []),
        ('_accumulate', False),
        ('_concurrent', False),
        ('_data', None),
    )

    def _start(self):
        self._sentinel = None  # sentinel for order concurrency
        super(SignalStrategy, self)._start()

    def signal_add(self, sigtype, signal):
        self._signals[sigtype].append(signal)

    def _notify(self, qorders=[], qtrades=[]):
        # Nullify the sentinel if done
        procorders = qorders or self._orderspending
        if self._sentinel is not None:
            for order in procorders:
                if order == self._sentinel and not order.alive():
                    self._sentinel = None
                    break

        super(SignalStrategy, self)._notify(qorders=qorders, qtrades=qtrades)

    def _next_catch(self):
        self._next_signal()
        if hasattr(self, '_next_custom'):
            self._next_custom()

    def _next_signal(self):
        if self._sentinel is not None and not self.p._concurrent:
            return  # order active and more than 1 not allowed

        sigs = self._signals
        nosig = [[0.0]]

        # Calculate current status of the signals
        ls_long = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_LONGSHORT] or nosig)
        ls_short = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_LONGSHORT] or nosig)

        l_enter0 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_LONG] or nosig)
        l_enter1 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_LONG_INV] or nosig)
        l_enter2 = all(x[0] for x in sigs[bt.SIGNAL_LONG_ANY] or nosig)
        l_enter = l_enter0 or l_enter1 or l_enter2

        s_enter0 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_SHORT] or nosig)
        s_enter1 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_SHORT_INV] or nosig)
        s_enter2 = all(x[0] for x in sigs[bt.SIGNAL_SHORT_ANY] or nosig)
        s_enter = s_enter0 or s_enter1 or s_enter2

        l_ex0 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_LONGEXIT] or nosig)
        l_ex1 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_LONGEXIT_INV] or nosig)
        l_ex2 = all(x[0] for x in sigs[bt.SIGNAL_LONGEXIT_ANY] or nosig)
        l_exit = l_ex0 or l_ex1 or l_ex2

        s_ex0 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_SHORTEXIT] or nosig)
        s_ex1 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_SHORTEXIT_INV] or nosig)
        s_ex2 = all(x[0] for x in sigs[bt.SIGNAL_SHORTEXIT_ANY] or nosig)
        s_exit = s_ex0 or s_ex1 or s_ex2

        # Use oppossite signales to start reversal (by closing)
        # but only if no "xxxExit" exists
        l_rev = not self._longexit and s_enter
        s_rev = not self._shortexit and l_enter

        # Opposite of individual long and short
        l_leav0 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_LONG] or nosig)
        l_leav1 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_LONG_INV] or nosig)
        l_leav2 = all(x[0] for x in sigs[bt.SIGNAL_LONG_ANY] or nosig)
        l_leave = l_leav0 or l_leav1 or l_leav2

        s_leav0 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_SHORT] or nosig)
        s_leav1 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_SHORT_INV] or nosig)
        s_leav2 = all(x[0] for x in sigs[bt.SIGNAL_SHORT_ANY] or nosig)
        s_leave = s_leav0 or s_leav1 or s_leav2

        # Invalidate long leave if longexit signals are available
        l_leave = not self._longexit and l_leave
        # Invalidate short leave if shortexit signals are available
        s_leave = not self._shortexit and s_leave

        # Take size and start logic
        size = self.getposition(self._dtarget).size
        if not size:
            if ls_long or l_enter:
                self._sentinel = self.buy(self._dtarget)

            elif ls_short or s_enter:
                self._sentinel = self.sell(self._dtarget)

        elif size > 0:  # current long position
            if ls_short or l_exit or l_rev or l_leave:
                # closing position - not relevant for concurrency
                self.close(self._dtarget)

            if ls_short or l_rev:
                self._sentinel = self.sell(self._dtarget)

            if ls_long or l_enter:
                if self.p._accumulate:
                    self._sentinel = self.buy(self._dtarget)

        elif size < 0:  # current short position
            if ls_long or s_exit or s_rev or s_leave:
                # closing position - not relevant for concurrency
                self.close(self._dtarget)

            if ls_long or s_rev:
                self._sentinel = self.buy(self._dtarget)

            if ls_short or s_enter:
                if self.p._accumulate:
                    self._sentinel = self.sell(self._dtarget)
