# 欢迎补充错误码
# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import json
import sentry_sdk

import datetime

ERRNO_DICT = {
    False: '抢票失败'
}


def withTimeString(string):
    return f"{datetime.datetime.now()}: {string}"
