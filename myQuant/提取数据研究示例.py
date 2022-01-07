# coding=utf-8
"""
# https://www.myquant.cn/docs/python/quickstart#e58306ddb2d2facd

"""
from __future__ import print_function, absolute_import
from gm.api import *

# 可以直接提取数据，掘金终端需要打开，接口取数是通过网络请求的方式，效率一般，行情数据可通过subscribe订阅方式
# 设置token， 查看已有token ID,在用户-密钥管理里获取
# set_token('your token_id')
set_token('e85fb3ce49e6aee3a7fabbadeb90d9c26a193c6e')
set_token('e85fb3ce49e6aee3a7fabbadeb90d9c26a193c6e')

if __name__ == '__main__':
    # 查询历史行情, 采用定点复权的方式， adjust指定前复权，adjust_end_time指定复权时间点
    data = history(symbol='SHSE.600000', frequency='1d', start_time='2020-01-01 09:00:00',
                   end_time='2020-12-31 16:00:00',
                   fields='open,high,low,close,volume', adjust=ADJUST_PREV, adjust_end_time='2020-12-31', df=True)
    print(data)
