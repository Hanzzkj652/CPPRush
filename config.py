# Copyright (c) 2024-2025 Hazzkj. All rights reserved.import json

import os
import sys

import loguru

from tool.CppRequest import CppRequest
from tool.Valuekey import Valuekey
from tool.TimeService import TimeService


# 创建通知器实例

# 获取图标文件的路径
def get_application_path():
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(os.path.realpath(sys.executable))
    else:
       application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

def get_application_tmp_path():
    return get_application_path()

BASE_DIR = get_application_path()
APP_PATH = BASE_DIR
TEMP_PATH = BASE_DIR

# loguru.logger.info(f"设置路径, APP_PATH={APP_PATH} TEMP_PATH={TEMP_PATH} BASE_DIR={BASE_DIR}")
os.makedirs(os.path.join(BASE_DIR, "configs"), exist_ok=True)
configDB = Valuekey(os.path.join(BASE_DIR, "configs", "config.json"))
if not configDB.contains("cookie_path"):
    configDB.insert("cookie_path", os.path.join(BASE_DIR, "configs", "cookies.json"))
main_request = CppRequest(cookies_config_path=configDB.get("cookie_path"))
global_cookiesconfig = main_request.Cookiesconfig

## 时间
time_service = TimeService()
time_service.set_timeoffset(time_service.compute_timeoffset())
