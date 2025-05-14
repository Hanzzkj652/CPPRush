import json
import os
import re
import inquirer

from datetime import datetime
from urllib.parse import urlparse, parse_qs
from loguru import logger

from config import main_request, get_application_path

buyer_value = []
addr_value = []
ticket_value = []
project_name = []
ticket_str_list = []

def convert_timestamp_to_str(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

def filename_filter(filename):
    filename = re.sub('[\\/\\:*?"<>|]', '', filename)
    return filename

def extract_id_from_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('eventMainId', [None])[0] or query_params.get('event', [None])[0]

def settings_cli():
    logger.warning("\n提示：请确保已在 https://cp.allcpp.cn/ticket/prePurchaser 配置购买人信息")
    
    # 修改为提供选择：使用默认URL或输入自定义URL
    questions = [
        inquirer.List('url_choice',
                    message='请选择票务来源',
                    choices=[
                        '使用指定活动(ID: 4670)即CP31',
                        '输入自定义网址'
                    ])
    ]
    
    url_answer = inquirer.prompt(questions)
    
    if url_answer['url_choice'] == '使用指定活动(ID: 4670)':
        ticket_url = "https://www.allcpp.cn/allcpp/ticket/getTicketTypeList.do?eventMainId=4670"
        ticket_id = "4670"
    else:
        # 用户选择输入自定义URL
        questions = [
            inquirer.Text('ticket_url',
                        message='请输入想要抢票的网址',
                        validate=lambda _, x: 'http' in x or 'https' in x)
        ]
        answers = inquirer.prompt(questions)
        ticket_url = answers['ticket_url']
        ticket_id = extract_id_from_url(ticket_url)
    
    if not ticket_id:
        logger.error("错误：无效的网址，未能提取活动ID")
        return
        
    try:
        logger.info(f"正在获取活动ID: {ticket_id}的票务信息...")
        ret = main_request.get(
            url=f"https://www.allcpp.cn/allcpp/ticket/getTicketTypeList.do?eventMainId={ticket_id}"
        ).json()
        
        if "ticketMain" not in ret:
            logger.error("错误：无法获取活动信息")
            return
            
        ticketMain = ret['ticketMain']
        ticketTypeList = ret["ticketTypeList"]
        global project_name, ticket_str_list, ticket_value
        project_name = ticketMain['eventName']
        
        logger.info(f"活动名称：{project_name}")
        logger.info(f"活动描述：{ticketMain['description']}")
        logger.info(f"详细信息：{ticketMain['eventDescription']}")

        # 构建票种表格数据和选项
        ticket_table = []
        ticket_choices = []
        ticket_str_list = []
        for ticket in ticketTypeList:
            name = ticket['ticketName']
            start_time = convert_timestamp_to_str(ticket['sellStartTime'])
            end_time = convert_timestamp_to_str(ticket['sellEndTime'])
            description = ticket['ticketDescription']
            ticket_id = ticket['id']
            
            # 添加场次信息（如果存在）
            square_info = ""
            if 'square' in ticket and ticket['square']:
                square_info = f" [{ticket['square']}]"
            
            ticket_table.append({
                'name': name,
                'start_time': start_time,
                'end_time': end_time,
                'description': description,
                'id': ticket_id,
                'square': ticket.get('square', '')
            })
            
            # 构建票种显示信息，包含场次和ID
            ticket_info = f"{name}{square_info} (ID:{ticket_id}, {start_time}开售)"
            ticket_str = f"{name}{square_info} | {start_time} | {end_time} | {description}"
            ticket_choices.append(ticket_info)
            ticket_str_list.append(ticket_str)

        ticket_value = [ticket['id'] for ticket in ticketTypeList]
        
        # 输出所有票种信息用于调试
        logger.debug("所有可用票种信息：")
        for i, ticket in enumerate(ticket_table):
            square = f" [{ticket['square']}]" if ticket['square'] else ""
            logger.debug(f"{i+1}. {ticket['name']}{square} (ID:{ticket['id']}, {ticket['start_time']}开售)")
        
        global buyer_value
        buyer_value = main_request.get(
            url=f"https://www.allcpp.cn/allcpp/user/purchaser/getList.do"
        ).json()
        
        buyer_str_list = [
            f"{item['realname']}-{item['idcard']}-{item['mobile']}"
            for item in buyer_value
        ]
        
        if not buyer_str_list:
            logger.error("错误：未找到购买人信息，请先在网站配置")
            return

        questions = [
            inquirer.List('ticket_type',
                         message='请选择票种（使用上下键选择，回车确认）',
                         choices=ticket_choices,
                         carousel=True),
            inquirer.Checkbox('buyers',
                            message='请选择购买人（可多选）',
                            choices=buyer_str_list)
        ]
        
        answers = inquirer.prompt(questions)
        if not answers['buyers']:
            logger.error("错误：至少需要选择一个购买人")
            return
            
        # 提取所选票种的ID
        selected_ticket_info = answers['ticket_type']
        selected_ticket_id = int(re.search(r'ID:(\d+)', selected_ticket_info).group(1))
        
        # 找到与ID对应的索引
        ticket_index = ticket_value.index(selected_ticket_id)
        buyer_indices = [buyer_str_list.index(buyer) for buyer in answers['buyers']]
        
        # 添加场次信息到配置详情
        selected_ticket = ticket_table[ticket_index]
        square_info = f" [{selected_ticket['square']}]" if selected_ticket['square'] else ""
        detail = f'{project_name}-{selected_ticket["name"]}{square_info}-{selected_ticket["start_time"]}'
        
        config = {
            'detail': detail,
            'tickets': selected_ticket_id,
            'people_cur': [buyer_value[i] for i in buyer_indices]  # 修复此处
        }
        
        config_dir = os.path.join(os.getcwd(), "configs")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, filename_filter(detail) + ".json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
            
        logger.success(f"配置已保存到：{config_path}")
        logger.debug("配置内容：")
        logger.debug(json.dumps(config, ensure_ascii=False, indent=2))
        logger.info("按回车键返回主菜单...")
        input()
        
    except Exception as e:
        logger.error(f"配置生成失败：{str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        logger.info("按回车键返回主菜单...")
        input()