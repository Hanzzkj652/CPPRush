import requests
import certifi
import time
import sys

from loguru import logger


version = "v1.0.4"

def check_version():
    """版本更新检查"""
    try:
        url = f"https://api.github.com/repos/Hanzzkj652/CPPRush/releases/latest"
        response = requests.get(url, 
                               timeout=5, 
                               verify=certifi.where(),
                               ) 
        # response.raise_for_status()
        current_version = version
        if response.status_code == 200:
            latest_info = response.json()
            latest_ver = latest_info.get("tag_name", "v0.0.0")
            if latest_ver > current_version:
                logger.warning(f"⚠️ 检测到新版本")
                logger.info(f"📦 当前版本: {current_version},🆕 最新版本: {latest_ver}")
                logger.info(f"📝 更新说明: {latest_info.get('body', '暂无更新说明')}")
                logger.error(f"❗ 请更新到最新版本后再使用，按回车退出程序")
                input()
                sys.exit(1)
            else:
                logger.success(f"当前版本 {current_version}，已是最新版本")
        else:
            logger.error(f"版本检查失败: HTTP {response.status_code},请检查网络连接")
            time.sleep(10)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.error(f"版本检查网络错误: {e}")
        time.sleep(10)
        sys.exit(1)
    except Exception as e:
        logger.error(f"版本检查出错: {str(e)}")
        time.sleep(10)
        sys.exit(1)


