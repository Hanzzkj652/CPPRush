# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import os
import inquirer
import sys
import time

from loguru import logger

from config import config, main_request, global_cookiesconfig
from tool.UtilityService import Valuekey
from policy.logging_config import capture_action, set_user_context


def login_cli():
    # 替换 configDB 为 config
    current_account = main_request.get_request_name()
    current_cookie_file = config.get("cookie_path")
    logger.success(f"当前账号：{current_account}")
    # 登录选项
    questions = [
        inquirer.List('action',
                      message='请选择操作',
                      choices=[
                          '新账号登录',
                          '导入登录信息文件',
                          '返回主菜单'
                      ])
    ]
    
    answers = inquirer.prompt(questions)
    if answers['action'] == '新账号登录':
        # 注销当前账号
        main_request.db.delete("cookie")
        logger.info("已注销当前账号，请在控制台完成登录...")
        
        try:
            main_request.get_cookies_str_force()
            logger.success(f"登录成功！当前账号：{main_request.get_request_name()}")
            # 设置用户上下文并记录登录成功
            set_user_context(main_request.get_request_name())
            capture_action("login_success")

            return True

        except Exception as e:
            logger.exception(f"登录失败：{str(e)}")
    
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
                main_request.cookies_config_path = new_cookie_file
                main_request.db = Valuekey(new_cookie_file)
                
                username = main_request.get_request_name()
                logger.success(f"导入成功！当前账号：{username}")
                set_user_context(username)
                capture_action("import_login_success", username=username, import_time=time.time())
            except Exception as e:
                logger.exception(f"导入失败：{str(e)}")

    
    return answers['action'] != '返回主菜单'