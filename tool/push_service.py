# Copyright (c) 2024-2025 Hazzkj. All rights reserved.

import json
import os
import requests
import sentry_sdk
from loguru import logger
from config import get_application_tmp_path


class PushService:
    """统一推送服务类，支持PushPlus和ServerChan"""
    
    @staticmethod
    def send_pushplus(token, content, title):
        """发送PushPlus消息"""
        try:
            url = "http://www.pushplus.plus/send"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "token": token,
                "content": content,
                "title": title
            }
            requests.post(url, headers=headers, data=json.dumps(data))
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.error("PushPlus消息发送失败")
    
    @staticmethod
    def send_serverchan(token, desp, title):
        """发送ServerChan消息"""
        try:
            url = f"https://sctapi.ftqq.com/{token}.send"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "desp": desp,
                "title": title
            }
            requests.post(url, headers=headers, data=json.dumps(data))
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.error("Server酱消息发送失败")
