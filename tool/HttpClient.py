# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import json
import time
import os
import requests
import sentry_sdk
from loguru import logger
from tool.UtilityService import Valuekey


class HttpClient:
    """整合的HTTP客户端，包含请求和Cookie管理功能"""
    
    def __init__(self, headers=None, cookies_config_path=None):
        from config import get_application_path
        self.session = requests.Session()
        
        # cookies配置路径处理
        if cookies_config_path:
            self.cookies_config_path = cookies_config_path
        else:
            # 检查程序目录是否可写
            base_path = get_application_path()
            config_dir = os.path.join(base_path, "configs")
            test_path = os.path.join(config_dir, "write_test.tmp")
            
            try:
                os.makedirs(config_dir, exist_ok=True)
                with open(test_path, 'w') as f:
                    f.write("test")
                os.remove(test_path)
                self.cookies_config_path = os.path.join(config_dir, "cookies.json")
            except (PermissionError, IOError):
                # 如果不可写，使用用户主目录
                user_home = os.path.expanduser("~")
                app_config_dir = os.path.join(user_home, "CPPRush", "configs")
                os.makedirs(app_config_dir, exist_ok=True)
                self.cookies_config_path = os.path.join(app_config_dir, "cookies.json")
                logger.info(f"使用用户主目录存储cookies: {self.cookies_config_path}")
        
        # 确保cookies文件所在目录存在
        os.makedirs(os.path.dirname(self.cookies_config_path), exist_ok=True)
        logger.debug(f"Cookies配置路径: {self.cookies_config_path}")
        
        self.db = Valuekey(self.cookies_config_path)
        self.headers = headers or {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5,ja;q=0.4',
            'cookie': "", 
            'origin': 'https://cp.allcpp.cn',
            'priority': 'u=1, i',
            'referer': 'https://cp.allcpp.cn/',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
        }

    # HTTP请求方法
    def get(self, url, data=None):
        self.headers["cookie"] = self.get_cookies_str()
        response = self.session.get(url, data=data, headers=self.headers)
        response.raise_for_status()
        return response

    def post(self, url, data=None):
        self.headers["cookie"] = self.get_cookies_str()
        response = self.session.post(url, data=data, headers=self.headers)
        response.raise_for_status()
        return response

    def get_request_name(self):
        try:
            if not self.have_cookies():
                return "未登录"
            result = self.get("https://www.allcpp.cn/allcpp/circle/getCircleMannage.do").json()
            return result["result"]["joinCircleList"][0]["nickname"]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return "未登录"

    def refreshToken(self):
        self._refresh_token()

    # Cookie管理方法
    @logger.catch
    def _login_and_save_cookies(self, login_url="https://cp.allcpp.cn/#/login/main"):
        logger.info("开始填写登录信息")
        logger.info("输入手机号：")
        phone = input()
        logger.info("输入密码：")
        password = input()

        login_url = "https://user.allcpp.cn/api/login/normal"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5,ja;q=0.4',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'origin': 'https://cp.allcpp.cn',
            'priority': 'u=1, i',
            'referer': 'https://cp.allcpp.cn/',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
        }
        try:
            payload = f"account={phone}&password={password}&phoneAccountBindToken=undefined&thirdAccountBindToken=undefined"
            response = requests.request("POST", login_url, headers=headers, data=payload)
            res_json = response.json()
            logger.debug(f"登录响应体： {res_json}")
            if "token" in res_json:
                cookies_dict = response.cookies.get_dict()
                logger.debug(f"cookies: {cookies_dict}")
                self.db.insert("cookie", cookies_dict)
                self.db.insert("password", password)
                self.db.insert("phone", phone)
                
                return response.cookies
            else:
                logger.error("登录失败，请重新输入")
                logger.info("输入手机号：")
                phone = input()
                logger.info("输入密码：")
                password = input()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            return None

    def _refresh_token(self):
        login_url = "https://user.allcpp.cn/api/login/normal"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5,ja;q=0.4',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'origin': 'https://cp.allcpp.cn',
            'priority': 'u=1, i',
            'referer': 'https://cp.allcpp.cn/',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
        }
        phone = self.db.get("phone")
        password = self.db.get("password")
        payload = f"account={phone}&password={password}&phoneAccountBindToken=undefined&thirdAccountBindToken=undefined"
        response = requests.request("POST", login_url, headers=headers, data=payload)
        res_json = response.json()
        logger.info(f"刷新登录响应体： {res_json}")
        if "token" in res_json:
            cookies_dict = response.cookies.get_dict()
            logger.info(f"cookies: {cookies_dict}")
            self.db.insert("cookie", cookies_dict)
            return cookies_dict

    def get_cookies(self, force=False):
        if force:
            return self.db.get("cookie")
        if not self.db.contains("cookie") or not self.db.contains("password") or not self.db.contains("phone"):
            return self._login_and_save_cookies()
        else:
            return self.db.get("cookie")

    def have_cookies(self):
        return self.db.contains("cookie") and self.db.contains("password") and self.db.contains("phone")

    def get_cookies_str(self):
        cookies = self.get_cookies()
        cookies_str = ""
        for key in cookies.keys():
            cookies_str += key + "=" + cookies[key] + "; "
        return cookies_str

    def get_cookies_value(self, name):
        cookies = self.get_cookies()
        for cookie in cookies:
            if cookie["name"] == name:
                return cookie["value"]
        return None

    def get_config_value(self, name, default=None):
        if self.db.contains(name):
            return self.db.get(name)
        else:
            return default

    def set_config_value(self, name, value):
        self.db.insert(name, value)

    def get_cookies_str_force(self):
        self._login_and_save_cookies()
        return self.get_cookies_str()


