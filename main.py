# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import os
import questionary
import time
import sys
import json

from loguru import logger
from json import JSONDecodeError

from cli.settings import settings_cli
from cli.login import login_cli
from cli.order import order_cli
from cli.go import go_cli
from cli.push_config import push_config_cli
from policy.version import check_version, version
from policy.machineid import agree_terms
from policy.logging_config import setup_logging, set_user_context, capture_action


# 初始化日志系统和错误监控
setup_logging(debug=False)

# 记录程序启动事件
capture_action("program_start", version=version, startup_time=time.time())


def check_login():
    """检查用户是否已登录
    """
    try:
        # 检查配置文件路径
        from config import get_application_path
        config_path = os.path.join(get_application_path(), 'configs', 'cookies.json')
        if not os.path.exists(config_path):
            
            logger.warning("登录配置文件不存在")
            return False
            
        # 检查文件大小
        if os.path.getsize(config_path) == 0:
            logger.warning("登录配置文件为空")
            return False
            
        # 读取并验证配置文件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:  # 再次检查内容是否为空
                    logger.warning("登录配置文件内容为空")
                    return False
                config = json.loads(content)
                
        except json.JSONDecodeError as e:
            logger.error(f"登录配置文件格式无效: {str(e)}")
            return False
            
        # 验证配置文件基本结构
        if not isinstance(config, dict) or '_default' not in config:
            logger.warning("登录配置文件结构无效")
            return False
        
        # 验证登录凭证完整性
        try:
            credentials_valid = all(
                any(item.get('key') == cred and item.get('value')
                    for item in config['_default'].values())
                for cred in ('phone', 'password')
            )
            
            if not credentials_valid:
                logger.warning("登录凭证不完整")
                return False

            return True
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.error(f"验证登录凭证时发生错误: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"验证登录状态时发生未知错误: {str(e)}")
        return False


def main():
    try:
        # 确保必要的目录存在    
        base_dir = os.path.dirname(os.path.realpath(sys.executable)) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(base_dir, "configs")
        logs_dir = os.path.join(base_dir, "logs")
        qrcodes_dir = os.path.join(config_dir, "qrcodes")
        
        # 创建所有必要的目录结构
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(qrcodes_dir, exist_ok=True)
        
        agree_terms()

        # 检查版本更新
        check_version()

        # 主循环
        while True:

            # 检查是否需要登录
            if not check_login():
                logger.warning("⚠️ 未检测到登录凭证，请先进行登录。")
                login_cli()
                #不退出程序，登录成功后继续执行
                continue
            else:
                # 设置用户上下文
                from config import main_request
                username = main_request.get_request_name()
                set_user_context(username)
                
                # 记录用户自动登录成功事件
                capture_action("auto_login_success", username=username, login_time=time.time())
                
            selected = questionary.select(
                "请选择功能",
                choices=[
                    '抢票',
                    '配置管理',
                    '查看订单',
                    '登录管理',
                    '消息推送配置',
                    '退出程序'
                ],
                use_indicator=True
            ).ask()

            if selected is None:
                logger.info("用户取消操作")
                break
                
            if selected == '配置管理':
                settings_cli()
            elif selected == '抢票':
                go_cli()
            elif selected == '查看订单':
                order_cli()
            elif selected == '登录管理':
                login_cli()
            elif selected == '消息推送配置':
                push_config_cli()
            else:  # 退出程序
                # 记录程序终止事件
                capture_action("program_exit", exit_time=time.time(), exit_reason="user_choice")
                logger.info("感谢使用CPP抢票系统，再见！❤️")
                time.sleep(3)
                break
    except Exception as e:
        # 记录程序异常终止事件
        capture_action("program_crash", error_type=type(e).__name__, crash_time=time.time())
        logger.exception("发生未知错误")
        raise

if __name__ == "__main__":
    main()