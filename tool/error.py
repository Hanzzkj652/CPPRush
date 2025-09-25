# 欢迎补充错误码
# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import json
import sentry_sdk

import datetime

ERRNO_DICT = {
    False: '抢票失败',
    True: '抢票成功',
    -1: '系统错误',
    0: '处理中',
    1: '票已售罄',
    2: '该票种已达到购买上限',
    3: '账户登录失效',
    4: '同证件限购一张',
    5: '请求过于频繁',
    -99999: '系统繁忙'  # 添加系统繁忙的错误码
}


def withTimeString(string):
    return f"{datetime.datetime.now()}: {string}"
