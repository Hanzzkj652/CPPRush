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
        
        # 确保配置目录存在并可写
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 测试目录可写性
            test_file = os.path.join(self.config_dir, "write_test.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            # 确保qrcodes目录存在
            qrcodes_dir = os.path.join(self.config_dir, "qrcodes")
            os.makedirs(qrcodes_dir, exist_ok=True)
            
            self.cookie_path = os.path.join(self.config_dir, "cookies.json")
            
        except (PermissionError, IOError) as e:
            # 如果程序目录不可写，则使用用户主目录
            logger.warning(f"无法在程序目录创建配置: {e}，将使用用户主目录")
            user_home = os.path.expanduser("~")
            app_config_dir = os.path.join(user_home, "CPPRush")
            self.config_dir = os.path.join(app_config_dir, "configs")
            os.makedirs(self.config_dir, exist_ok=True)
            
            qrcodes_dir = os.path.join(self.config_dir, "qrcodes")
            os.makedirs(qrcodes_dir, exist_ok=True)
            
            self.cookie_path = os.path.join(self.config_dir, "cookies.json")
            logger.info(f"已将配置目录设置为: {self.config_dir}")
        
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
                    self.settings["cookie_path"] = self.cookie_path
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
