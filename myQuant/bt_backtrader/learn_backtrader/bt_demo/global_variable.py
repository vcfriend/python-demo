#!/usr/bin/env python3
# -*- coding:utf-8-*-
# 全局变量管理模块


def init():
    """在主模块初始化"""
    global GLOBALS_DICT
    GLOBALS_DICT = {}


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
