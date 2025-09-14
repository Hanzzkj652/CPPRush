# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import json
import os
import time
import inquirer
import qrcode
import sentry_sdk

from loguru import logger
from tabulate import tabulate
from PIL import Image
from datetime import datetime
from typing import List, Dict

from config import main_request
from policy.machineid import get_machine_id

def get_orders() -> List[Dict]:
    try:
        resp = main_request.get(
            url="https://www.allcpp.cn/api/tk/getList.do?type=0&sort=0&index=1&size=100"
        ).json()
        orders = resp["result"]["data"]
        return [{
            "id": order["id"],
            "eventName": order["eventName"],
            "ticketName": order["ticketName"],
            "ticketCount": order["ticketCount"],
            "price": order["price"],
            "payType": order["payType"],
            "createTime": datetime.utcfromtimestamp(order["createTime"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        } for order in orders]
    except Exception as e:
        logger.error(f"获取订单失败：{str(e)}")
        return []

def display_orders(orders: List[Dict]):
    if not orders:
        logger.error("未找到任何订单")
        return
    
    # 准备表格数据
    headers = ["序号", "活动名称", "票种", "数量", "价格（元）", "创建时间"]
    table_data = [
        [i+1, order["eventName"], order["ticketName"], 
         order["ticketCount"], f"{order['price']//100:,}", order["createTime"]]
        for i, order in enumerate(orders)
    ]
    
    # 使用tabulate生成美观的表格
    table = tabulate(
        table_data,
        headers=headers,
        tablefmt="grid",
        colalign=("center", "left", "left", "center", "right", "center"),
        maxcolwidths=[6, 30, 20, 6, 10, 20]
    )
    
    logger.info("订单列表：")
    for line in table.split('\n'):
        print(line)

def generate_qr_code(qr_data: str) -> str:
    qr = qrcode.QRCode()
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_image = qr.make_image()
    
    # 保存二维码图片到项目configs目录
    temp_dir = os.path.join(os.getcwd(), "configs", "qrcodes")
    os.makedirs(temp_dir, exist_ok=True)
    qr_path = os.path.join(temp_dir, "payment_qr.png")
    qr_image.save(qr_path)
    return qr_path

def order_cli():
    
    while True:
        questions = [
            inquirer.List('action',
                         message='请选择操作',
                         choices=[
                             '刷新订单列表',
                             '支付订单',
                             '返回主菜单'
                         ])
        ]
        
        answers = inquirer.prompt(questions)
        if answers['action'] == '刷新订单列表':
            orders = get_orders()
            display_orders(orders)
            
        elif answers['action'] == '支付订单':
            # orders = get_orders()
            if not orders:
                logger.info("没有可支付的订单")
                continue
                
            # display_orders(orders)
            
            questions = [
                inquirer.List('order_index',
                            message='请选择要支付的订单',
                            choices=[
                                f"{i}. {order['eventName']} - {order['ticketName']}"
                                for i, order in enumerate(orders)
                            ])
            ]
            
            order_answer = inquirer.prompt(questions)
            if order_answer:
                order_idx = int(order_answer['order_index'].split('.')[0])
                order = orders[order_idx]
                
                try:
                    url = f"https://www.allcpp.cn/allcpp/ticket/buyTicketForOrder.do?orderid={order['id']}&ticketInfo=undefined,{order['ticketCount']},{order['price']}&paytype={order['payType']}"
                    resp = main_request.post(url=url).json()
                    logger.info(f"支付订单响应：{resp}")
                    
                    if 'result' in resp and 'code' in resp['result']:
                        # 生成并显示二维码
                        qr_path = generate_qr_code(resp['result']['code'])
                        # 设置Sentry上下文信息
                        sentry_sdk.set_tag("machine_id", get_machine_id())
                        sentry_sdk.set_tag("username", main_request.get_request_name())
                        sentry_sdk.set_tag("action", "payment_qr_generated")
                        sentry_sdk.capture_message("用户订单支付二维码生成成功", level="info")
                        
                        # 使用系统默认图片查看器打开二维码
                        try:
                            Image.open(qr_path).show()
                        except Exception as e:
                            logger.warning(f"无法自动打开二维码图片：{str(e)}")


                        logger.info(f"请使用微信扫描二维码完成支付，二维码已保存到：{qr_path}")
                        logger.info("提示：如果无法打开图片，请手动复制路径在图片查看器中打开")
                    else:
                        logger.error("获取支付二维码失败，请稍后重试")
                        
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    logger.error(f"支付订单失败：{str(e)}")
        
        else:  # 返回主菜单
            break
    
    return False  # 表示要返回主菜单