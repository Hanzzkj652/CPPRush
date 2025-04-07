import os
import inquirer
import time
import sys
import json

from loguru import logger
from logtail import LogtailHandler
from json import JSONDecodeError

from cli.settings import settings_cli
from cli.login import login_cli
from cli.order import order_cli
from cli.go import go_cli

# 配置日志
logger.add("app.log")


def check_login():
    """检查用户是否已登录
    Returns:
        bool: 如果用户已登录且登录凭证有效则返回True，否则返回False
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
    # 确保必要的目录存在    
    base_dir = os.path.dirname(os.path.realpath(sys.executable))
    config_dir = os.path.join(base_dir, "configs")
    os.makedirs(config_dir, exist_ok=True)
    
    # 配置日志
    logger.add("app.log")



    # 主循环
    while True:

        # 检查是否需要登录
        if not check_login():
            logger.warning("⚠️ 未检测到登录凭证，请先进行登录。")
            login_cli()
            #不退出程序，登录成功后继续执行
            continue
        else:
            pass
            


        questions = [
            inquirer.List('action',
                         message='请选择功能',
                         choices=[
                             '抢票',
                             '配置管理',
                             '查看订单',
                             '登录管理',
                             '退出程序'
                         ])
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            break
            
        if answers['action'] == '配置管理':
            settings_cli()
        elif answers['action'] == '抢票':
            go_cli()
        elif answers['action'] == '查看订单':
            order_cli()
        elif answers['action'] == '登录管理':
            login_cli()
        else:  # 退出程序
            logger.info("感谢使用CPP抢票系统，再见！❤️")
            time.sleep(3)
            break

if __name__ == "__main__":

    main()