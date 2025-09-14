# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import inquirer
from loguru import logger
from config import config
from policy.logging_config import capture_action


def push_config_cli():
    """消息推送配置界面"""
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
    if push_answers is None:
        logger.info("用户取消操作")
        return False
        
    if push_answers:
        config.set("serverchanKey", push_answers['serverchan'])
        config.set("pushplusToken", push_answers['pushplus'])
        
        # 记录用户操作
        capture_action("push_config_saved")
        
        logger.success("推送配置已保存！")
        
        # 显示当前配置状态
        serverchan_status = "已配置" if push_answers['serverchan'] else "未配置"
        pushplus_status = "已配置" if push_answers['pushplus'] else "未配置"
        logger.info(f"Server酱状态：{serverchan_status}")
        logger.info(f"PushPlus状态：{pushplus_status}")
        
    logger.info("按回车键返回主菜单...")
    input()
    return True