#!/usr/bin/env python3
# -*- coding:utf-8-*-
# 全局变量,常量,枚举管理模块
from enum import Enum


def init():
    """在主模块初始化"""
    global GLOBALS_DICT
    GLOBALS_DICT = dict()


def set(name, value):
    """设置"""
    try:
        GLOBALS_DICT[name] = value
        return True
    except KeyError:
        return False


def get(name, default=None):
    """取值"""
    try:
        value = GLOBALS_DICT.get(name)
        return value if value else default
    except KeyError:
        return None


class TargetType(Enum):
    """枚举开仓类型"""
    T_SIZE = "数量"  # 成交量
    T_VALUE = "金额"  # 目标金额
    T_PERCENT = "百分比"  # 百分比


class Color:
    Black = 0
    Red = 1
    Green = 2
    Yellow = 3
    Blue = 4
    Magenta = 5
    Cyan = 6
    White = 7


class Mode:
    Foreground = 30
    Background = 40
    ForegroundBright = 90
    BackgroundBright = 100


def tcolor(c, m=Mode.Foreground):
    return '\033[{}m'.format(m + c)


def treset():
    return '\033[0m'
