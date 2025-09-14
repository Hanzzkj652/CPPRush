import os
import json
from machineid import id as machine_id
from loguru import logger

def get_machine_id():
    """获取或生成机器唯一标识"""
    try:
        # 使用 py-machineid 生成唯一标识
        unique_id = machine_id()
        
        # 保存到配置文件
        config_dir = os.path.join(os.getcwd(), 'configs')
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, 'config.json')
        
        # 读取现有配置
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if config.get('machine_id'):
                    return config['machine_id']
        
        # 添加机器ID到配置中
        config['machine_id'] = unique_id
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        return unique_id
        
    except Exception as e:
        logger.exception(f"生成机器ID失败: {str(e)}")
        return "unknown-device"
    
def agree_terms():
    """用户协议确认（支持重试）"""

    print("\033[1;36m欢迎使用CPPRush软件，使用前请阅读EULA( https://docs-cpprush.netlify.app/privacy/eula )。若您使用时遇到问题，请查阅使用文档( https://docs-cpprush.netlify.app/ )\033[0m")
    print(f"\033[1;33m⚠️ 免责声明：一旦您使用本工具，即视为您已同意并遵守网站中关于本工具的使用协议。\033[0m")