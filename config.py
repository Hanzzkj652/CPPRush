# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import json

import os
import sys
from pathlib import Path

from loguru import logger
from tool.HttpClient import HttpClient
from tool.UtilityService import TimeService


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
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """加载设置"""
        self.settings = {
            "cookie_path": self.cookie_path
        }
        
        # 从文件加载配置
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_settings = json.load(f)
                    self.settings.update(file_settings)
            except (json.JSONDecodeError, IOError) as e:
                logger.exception(f"加载配置文件失败: {str(e)}")

    def save_settings(self):
        """保存设置到文件"""
        try:
            save_settings = {k: v for k, v in self.settings.items() if k != "cookie_path"}
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(save_settings, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.exception(f"保存配置文件失败: {str(e)}")

    def get(self, key, default=None):
        """获取配置值"""
        return self.settings.get(key, default)

    def set(self, key, value):
        """设置配置值"""
        self.settings[key] = value
        self.save_settings()  # 自动保存

    def contains(self, key):
        """检查是否包含键"""
        return key in self.settings

BASE_DIR = get_application_path()
APP_PATH = BASE_DIR
TEMP_PATH = BASE_DIR

# 创建全局配置实例
config = Config()
main_request = HttpClient(cookies_config_path=config.cookie_path)
global_cookiesconfig = main_request

## 时间
time_service = TimeService()
time_service.set_timeoffset(time_service.compute_timeoffset())
