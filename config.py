# Copyright (c) 2024-2025 Hazzkj. All rights reserved.import json

import os
import sys
from pathlib import Path

from tool.CppRequest import CppRequest
from tool.TimeService import TimeService


# 获取图标文件的路径
def get_application_path():
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(os.path.realpath(sys.executable))
    else:
       application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

def get_application_tmp_path():
    return get_application_path()

class Config:
    def __init__(self):
        self.base_dir = get_application_path()
        self.config_dir = os.path.join(self.base_dir, "configs")
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.cookie_path = os.path.join(self.config_dir, "cookies.json")
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """加载设置"""
        self.settings = {
            "cookie_path": self.cookie_path
        }

    def get(self, key, default=None):
        """获取配置值"""
        return self.settings.get(key, default)

    def set(self, key, value):
        """设置配置值"""
        self.settings[key] = value

    def contains(self, key):
        """检查是否包含键"""
        return key in self.settings

BASE_DIR = get_application_path()
APP_PATH = BASE_DIR
TEMP_PATH = BASE_DIR

# 创建全局配置实例
config = Config()
main_request = CppRequest(cookies_config_path=config.cookie_path)
global_cookiesconfig = main_request.Cookiesconfig

## 时间
time_service = TimeService()
time_service.set_timeoffset(time_service.compute_timeoffset())
