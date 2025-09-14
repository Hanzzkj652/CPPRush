# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import sys
import os
from datetime import datetime
from pathlib import Path
from loguru import logger

import sentry_sdk
from sentry_sdk.integrations.loguru import LoguruIntegration

from policy.machineid import get_machine_id
from policy.version import version

# 默认日志级别，可修改此常量来改变默认行为
DEFAULT_LOG_LEVEL = "INFO"

def setup_logging(debug: bool = False):
    """
    配置日志系统和错误监控
    """
    # 初始化 Sentry 监控
    try:
        sentry_sdk.init(
            dsn="http://24177bc2d16c2442320fcd751966641d@sentry.vipzkjlk.pics/2",
            integrations=[
                LoguruIntegration(
                    level="INFO", 
                    event_level="WARNING"
                ),
            ],
            traces_sample_rate=1.0,
            debug=debug,
            environment="development" if debug else "production",
            release=version, 
            send_default_pii=False,
            attach_stacktrace=True,
            before_send=filter_sentry_events
        )
        
        # 设置机器标识和用户标识
        sentry_sdk.set_tag("machine_id", get_machine_id())

    except Exception as e:
        logger.warning(f"Sentry 初始化失败: {e}")
    
    # 获取机器ID简短标识用于日志
    machine_id_short = get_machine_id()[:8] if get_machine_id() else "unknown"
    
    # 移除默认处理器
    logger.remove()
    
    # 根据DEBUG模式或默认级别配置控制台输出
    if debug:
        logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>M:" + machine_id_short + "</cyan> - <level>{message}</level>",
            colorize=True
        )
    else:
        logger.add(
            sys.stdout,
            level=DEFAULT_LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>M:" + machine_id_short + "</cyan> - <level>{message}</level>",
            colorize=True
        )
    
    # 创建logs目录并配置文件日志
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = logs_dir / f"cpprush_{timestamp}.log"
    
    logger.add(
        str(log_filename),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | M:" + machine_id_short + " - {message}",
        retention="7 days",
        encoding="utf-8"
    )
    


def filter_sentry_events(event, hint):
    # 保留核心识别信息
    if 'user' in event:
        # 只保留必要的用户标识信息
        user_info = event['user']
        filtered_user = {
            'id': user_info.get('id'),
            'username': user_info.get('username')
        }
        event['user'] = filtered_user
    
    if 'contexts' in event:
        contexts = event['contexts']
        filtered_contexts = {}
        
        # 保留关键上下文
        for key in ['os', 'runtime', 'device']:
            if key in contexts:
                filtered_contexts[key] = contexts[key]
        
        # 保留自定义的配置信息，但简化内容
        if 'config_info' in contexts:
            config_info = contexts['config_info']
            filtered_contexts['config_info'] = {
                'buyer_count': config_info.get('buyer_count'),
                'action': config_info.get('action')
            }
        
        event['contexts'] = filtered_contexts
    
    # 移除敏感的额外数据
    if 'extra' in event:
        extra = event['extra']
        filtered_extra = {}
        
        # 只保留非敏感的调试信息
        for key in ['error_type', 'component', 'operation']:
            if key in extra:
                filtered_extra[key] = extra[key]
        
        event['extra'] = filtered_extra
    
    return event

def set_user_context(username: str = None):
    """
    设置用户上下文信息
    """
    if username:
        sentry_sdk.set_tag("username", username)
        sentry_sdk.set_user({"username": username})

def capture_action(action: str, **context):
    """
    捕获用户操作事件
    """
    sentry_sdk.set_tag("action", action)
    if context:
        sentry_sdk.set_context("action_context", context)
    sentry_sdk.capture_message(f"用户操作: {action}", level="info")