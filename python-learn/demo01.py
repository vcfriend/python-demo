from datetime import datetime

global now_datetime


def init():
    global now_datetime
    now_datetime = None
    pass


def show_datetime():
    now_datetime = datetime.now()
    print('当前时间:', now_datetime)
    return now_datetime


"""-------主函数---------"""
if __name__ == '__main__':
    show_datetime()
