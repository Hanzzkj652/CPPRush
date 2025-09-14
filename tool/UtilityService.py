# Copyright (c) 2024-2025 Hazzkj. All rights reserved.
import json
import ntplib
import time
import sentry_sdk
from loguru import logger
from tinydb import TinyDB, Query


class TimeService:
    def __init__(self, _ntp_server="ntp.aliyun.com") -> None:
        self.ntp_server = _ntp_server
        self.client = ntplib.NTPClient()
        self.timeoffset: float = 0

    def compute_timeoffset(self) -> str:
        """
        返回的timeoffset单位为秒
        """
        # NTP时间请求有可能会超时失败, 设定三次重试机会
        for i in range(0, 3):
            try:
                response = self.client.request(self.ntp_server, version=4)
                break
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.warning("第" + str(i + 1) + "次获取NTP时间失败, 尝试重新获取")
                if i == 2:
                    return "error"
                time.sleep(0.5)

        return format(-(response.offset), ".5f")

    def set_timeoffset(self, _timeoffset: str) -> None:
        """
        传入的timeoffset单位为秒
        """
        if _timeoffset == "error":
            self.timeoffset = 0
            logger.warning("NTP时间同步失败, 使用本地时间")
        else:
            self.timeoffset = float(_timeoffset)
            
    def get_timeoffset(self) -> float:
        """
        获取到的timeoffset单位为秒
        """
        return self.timeoffset


class Valuekey:
    def __init__(self, db_path='kv_db.json'):
        self.db = TinyDB(db_path, indent=4)
        self.KeyValue = Query()

    def insert(self, key, value):
        # 如果键已经存在，更新其值；否则插入新键值对
        if self.db.contains(self.KeyValue.key == key):
            self.db.update({'value': value}, self.KeyValue.key == key)
        else:
            self.db.insert({'key': key, 'value': value})

    def get(self, key):
        try:
            result = self.db.get(self.KeyValue.key == key)
            return result['value'] if result else None
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return None

    def update(self, key, value):
        try:
            if self.db.contains(self.KeyValue.key == key):
                self.db.update({'value': value}, self.KeyValue.key == key)
            else:
                raise KeyError(f"Key '{key}' not found in database.")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise

    def delete(self, key):
        try:
            self.db.remove(self.KeyValue.key == key)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise

    def contains(self, key):
        return self.db.contains(self.KeyValue.key == key)