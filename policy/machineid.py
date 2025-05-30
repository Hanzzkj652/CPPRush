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
        config_path = os.path.join(config_dir, 'machine_config.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                if config.get('machine_id'):
                    return config['machine_id']
        
        # 保存新生成的ID
        config = {'machine_id': unique_id}
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        return unique_id
        
    except Exception as e:
        logger.error(f"生成机器ID失败: {str(e)}")
        return "unknown-device"
    
def agree_terms():
    """用户协议确认（支持重试）"""

    print("\033[1;36m欢迎使用CPPRush软件，使用前请阅读EULA( https://docs-cpprush.netlify.app/privacy/eula )。若您使用时遇到问题，请查阅使用文档( https://docs-cpprush.netlify.app/ )\033[0m")
    print(f"\033[1;33m⚠️ 免责声明：一旦您使用本工具，即视为您已同意并遵守网站中关于本工具的使用协议。\033[0m")
    # 循环验证输入
    while True: 

        logger.info(f"请阅读网站中的EULA,并键入: 我已阅读并同意EULA,黄牛倒卖狗死妈")
        user_input = input().strip()    
        if "同意" in user_input and "黄牛" in user_input and "死妈" in user_input:
  
            logger.success(f"✅ 您已阅读同意并遵守EULA，程序将继续运行。")
            return   

        logger.error(f"❌ 您未阅读并同意EULA，请重新输入以继续。")