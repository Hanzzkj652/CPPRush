import hashlib
import json
import os
import secrets
import string
import time
import sys

from datetime import datetime
from json import JSONDecodeError
from urllib.parse import quote

import inquirer
import qrcode
import retry
from loguru import logger
from requests import HTTPError, RequestException

from config import main_request, configDB, time_service
from tool import PushPlus
from tool import ServerChan
from tool.error import ERRNO_DICT
def format_dictionary_to_string(data):
    formatted_string_parts = []
    for key, value in data.items():
        if isinstance(value, list) or isinstance(value, dict):
            formatted_string_parts.append(
                f"{quote(key)}={quote(json.dumps(value, separators=(',', ':'), ensure_ascii=False))}"
            )
        else:
            formatted_string_parts.append(f"{quote(key)}={quote(str(value))}")

    formatted_string = "&".join(formatted_string_parts)
    return formatted_string

def load_config_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败：{str(e)}")
        return None

def generate_qr_code(qr_data):
    qr = qrcode.QRCode()
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_image = qr.make_image()
    temp_dir = os.path.join(os.getcwd(), "configs", "qrcodes")
    os.makedirs(temp_dir, exist_ok=True)
    qr_path = os.path.join(temp_dir, "payment_qr.png")
    qr_image.save(qr_path)
    return qr_path

def go_cli():
    isRunning = True
    
    base_dir = os.path.dirname(os.path.realpath(sys.executable))
    config_dir = os.path.join(base_dir, "configs")
    os.makedirs(config_dir, exist_ok=True)
    config_files = [f for f in os.listdir(config_dir) if f.endswith('.json') and f not in {'config.json', 'cookies.json','machine_config.json'}]
    
    if not config_files:
        logger.error("未找到任何配置文件，请先在'配置管理'中创建配置")
        logger.info("按回车键返回主菜单...")
        input()
        return False
    
    def format_config_filename(filename):
        # 移除.json后缀
        name = filename.replace('.json', '')
        
        # 尝试从文件名中提取活动名称和时间信息
        if ' - ' in name:
            # 处理带有时间信息的格式
            parts = name.split(' - ')
            event_name = parts[0].strip()
            # 如果活动名称过长，截断并添加省略号
            if len(event_name) > 25:
                event_name = event_name[:22] + '...'
        else:
            # 处理不带时间信息的格式
            event_name = name
            if len(event_name) > 25:
                event_name = event_name[:22] + '...'
        
        # 尝试提取时间信息
        time_info = None
        for part in name.split():
            if len(part) == 6 and part.isdigit():  # 匹配时间格式HHMMSS
                time_info = part
                break
        
        # 返回格式化后的显示名称
        if time_info:
            return f"{event_name} ({time_info})"
        return event_name
    
    # 创建文件名映射关系
    filename_map = {format_config_filename(f): f for f in config_files}
    
    # 选择配置文件
    questions = [
        inquirer.List('config_file',
                      message='请选择要使用的配置文件',
                      choices=list(filename_map.keys()),
                      carousel=True),
        inquirer.Text('start_time',
                     message='请输入抢票时间（格式：YYYY-MM-DD HH:mm:ss，留空则立即开始）',
                     validate=lambda _, x: not x or datetime.strptime(x, '%Y-%m-%d %H:%M:%S')),
        inquirer.Text('interval',
                     message='请输入抢票间隔（毫秒）',
                     validate=lambda _, x: x.isdigit() and int(x) >= 1,
                     default='300'),
        inquirer.List('mode',
                     message='请选择抢票模式',
                     choices=['无限', '有限']),
        inquirer.Text('attempts',
                     message='请输入抢票次数（仅限有限模式）',
                     validate=lambda _, x: x.isdigit() and int(x) >= 1,
                     default='100',
                     ignore=lambda x: x.get('mode') == '无限')
    ]
    
    answers = inquirer.prompt(questions)
    if not answers:
        return False
    
    # 加载配置文件
    original_filename = filename_map.get(answers['config_file'])
    if not original_filename:
        logger.error("无法找到对应的配置文件")
        logger.info("按回车键返回主菜单...")
        input()
        return False
        
    config_path = os.path.join(config_dir, original_filename)
    tickets_info = load_config_file(config_path)
    if not tickets_info:
        logger.info("按回车键返回主菜单...")
        input()
        return False
    
    # 转换时间格式
    start_time = answers['start_time']
    if start_time:
        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')
    
    interval = int(answers['interval'])
    mode = 0 if answers['mode'] == '无限' else 1
    total_attempts = int(answers.get('attempts', 100))
    left_time = total_attempts
    
    try:
        # 等待开始时间
        if start_time:
            logger.info("等待开始时间")
            timeoffset = time_service.get_timeoffset()
            logger.info(f"时间偏差已被设置为: {timeoffset}s")
            
            while isRunning:
                time_difference = (
                    datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S").timestamp()
                    - time.time() + timeoffset
                )
                
                if time_difference > 0:
                    if time_difference > 5:
                        # 当剩余时间大于5秒时显示等待信息
                        logger.info(f"等待中，剩余等待时间: {int(time_difference)}秒")
                        time.sleep(1)
                    else:
                        # 剩余5秒时停止输出，进入精确等待
                        logger.info('即将开抢')
                        start_time = time.perf_counter()
                        end_time = start_time + time_difference
                        while time.perf_counter() < end_time:
                            pass
                        break
                else:
                    break
        
        # 开始抢票
        people_cur = tickets_info["people_cur"]
        ticket_id = tickets_info["tickets"]
        @retry.retry(exceptions=RequestException, tries=60, delay=interval / 1000)
        def inner_request():
            nonlocal isRunning
            if not isRunning:
                raise ValueError("抢票已停止")

            timestamp = int(time.time())
            n = string.ascii_letters + string.digits
            nonce = ''.join(secrets.choice(n) for i in range(32))
            sign = hashlib.md5(f"2x052A0A1u222{timestamp}{nonce}{ticket_id}2sFRs".encode('utf-8')).hexdigest()

            ret = main_request.post(
                url=f"https://www.allcpp.cn/allcpp/ticket/buyTicketWeixin.do?ticketTypeId={ticket_id}"
                    f"&count={len(people_cur)}&nonce={nonce}&timeStamp={timestamp}&sign={sign}&payType=0&"
                    f"purchaserIds={','.join([str(p['id']) for p in people_cur])}",
            ).json()
            
            err = ret["isSuccess"]
            logger.debug(f'状态码: {err}({ERRNO_DICT.get(err, "未知错误码")}), 请求体: {ret}')
            
            if ret["message"] == "同证件限购一张！":
                isRunning = False
                raise ValueError("同证件限购一张！")

            if ret["message"] == "请求过于频繁，请稍后再试":
                logger.info("出现风控，重新登录")

            if not ret["isSuccess"]:
                raise HTTPError("重试次数过多，重新准备订单")
                
            return ret, err
        
        while isRunning:
            try:
                request_result, errno = inner_request()
                left_time_str = "无限" if mode == 0 else f"{left_time}/{total_attempts}"
                logger.info(f"抢票进度：第{total_attempts - left_time + 1}次尝试，状态：{ERRNO_DICT.get(errno, '未知错误码')}，剩余次数：{left_time_str}")

                if errno:
                    logger.success("抢票成功😊！生成支付二维码...")
                    # 生成并显示二维码
                    qr = qrcode.QRCode()
                    qr.add_data(request_result['result']['code'])
                    qr.make(fit=True)
                    qr_image = qr.make_image()
                    qr_path = os.path.join(base_dir, "configs", "qrcodes", "payment_qr.png")
                    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
                    qr_image.save(qr_path)
                    # 在控制台打印二维码
                    qr.print_ascii()
                    # 使用系统默认程序打开二维码图片
                    os.startfile(qr_path)

                    logger.info(f"请使用微信扫描二维码完成支付，二维码已保存到：{qr_path}")
                    
                    # 发送通知
                    pushplusToken = configDB.get("pushplusToken")
                    if pushplusToken:
                        PushPlus.send_message(pushplusToken, "恭喜您抢票成功", "付款吧")
                        
                    serverchanKey = configDB.get("serverchanKey")
                    if serverchanKey:
                        ServerChan.send_message(serverchanKey, "恭喜您抢票成功", "付款吧")
        
                    
                    break
                    
                if mode == 1:
                    left_time -= 1
                    if left_time <= 0:
                        logger.warning("已达到最大尝试次数，抢票结束")
                        isRunning = False
                        break
                        
            except (ValueError, HTTPError) as e:
                logger.error(f"错误：{str(e)}")
                if str(e) == "同证件限购一张！":
                    break
            except Exception as e:
                logger.exception(e)
                logger.error(f"发生错误：{str(e)}")

            time.sleep(interval / 1000.0)
    
    except KeyboardInterrupt:
        logger.info("已手动停止抢票")
    except Exception as e:
        logger.exception(e)
        logger.error(f"发生错误：{str(e)}")

    logger.info("按回车键返回主菜单...")
    input()
    return False