# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import os
import inquirer
import sys
import time

from loguru import logger

from config import config, main_request, global_cookiesconfig
from tool.Valuekey import Valuekey


def login_cli():
    # 替换 configDB 为 config
    current_account = main_request.get_request_name()
    current_cookie_file = config.get("cookie_path")
    logger.success(f"当前账号：{current_account}")
    logger.debug(f"当前登录信息文件：{current_cookie_file if current_cookie_file else '无'}")
    
    # 登录选项
    questions = [
        inquirer.List('action',
                      message='请选择操作',
                      choices=[
                          '新账号登录',
                          '导入登录信息文件',
                          '配置消息推送',
                          '返回主菜单'
                      ])
    ]
    
    answers = inquirer.prompt(questions)
    
    if answers['action'] == '新账号登录':
        # 注销当前账号
        main_request.Cookiesconfig.db.delete("cookie")
        logger.info("已注销当前账号，请在控制台完成登录...")
        
        try:
            main_request.Cookiesconfig.get_cookies_str_force()
            logger.success(f"登录成功！当前账号：{main_request.get_request_name()}")

            return True

        except Exception as e:
            logger.error(f"登录失败：{str(e)}")
    
    elif answers['action'] == '导入登录信息文件':
        questions = [
            inquirer.Path('cookie_file',
                        message='请输入登录信息文件路径',
                        exists=True,
                        path_type=inquirer.Path.FILE)
        ]
        
        file_answer = inquirer.prompt(questions)
        if file_answer:
            try:
                # 复制登录信息文件
                import shutil
                cookie_file = file_answer['cookie_file']
                new_cookie_file = os.path.join(os.getcwd(), "configs", "cookies.json")
                shutil.copy2(cookie_file, new_cookie_file)
                
                # 更新配置
                config.set("cookie_path", new_cookie_file)
                main_request.Cookiesconfig = global_cookiesconfig
                
                logger.success(f"导入成功！当前账号：{main_request.get_request_name()}")
            except Exception as e:
                logger.error(f"导入失败：{str(e)}")
    
    elif answers['action'] == '配置消息推送':
        logger.info("提示：留空则不启用对应的推送服务")
        
        questions = [
            inquirer.Text('serverchan',
                        message='Server酱SendKey (https://sct.ftqq.com/)',
                        default=config.get("serverchanKey") or ''),
            inquirer.Text('pushplus',
                        message='PushPlus Token (https://www.pushplus.plus/)',
                        default=config.get("pushplusToken") or '')
        ]
        
        push_answers = inquirer.prompt(questions)
        if push_answers:
            config.insert("serverchanKey", push_answers['serverchan'])
            config.insert("pushplusToken", push_answers['pushplus'])
            logger.success("推送配置已保存！")
    
    return answers['action'] != '返回主菜单'