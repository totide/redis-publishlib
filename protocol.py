# -*- coding: utf-8 -*-

import time
import json
import urllib
import random

from conf import ACCEPTER
from action import MessageAction
from helper import RedisHelper, redis_helper


class Message(object):
    """Redis message
         
    message content format:  '{"args": [0, "all", "hello world", {}], "class": "MailGlobal", "func": "AddMailToAll"}'
    """
    EXPIRED_CHANNELS = RedisHelper.EXPIRED_CHANNELS
    TIMER_EVENT_KEY = RedisHelper.TIMER_EVENT_KEY

    @staticmethod
    def read(type, channel, content):
        is_timer_event = False
        original_content = content
        try:
            if channel in Message.EXPIRED_CHANNELS:
                # timer event trigger
                content = json.loads(redis_helper.conn.hget(Message.TIMER_EVENT_KEY, content))
                is_timer_event = True
            else:
                content = json.loads(content)
        except Exception as e:
            print('[Publish Message] read error: %r' % (e))
            return

        # 有消息id字段
        msg_id = content.get("__id__", "")
        if msg_id:
            try:
                content = json.loads(redis_helper.conn.get(msg_id))
                if content.get("is_read", 0):
                    return
            except Exception as e:
                print('[Publish Message] read msg_id[%s] error: %r' % (msg_id, e))
                return

        # 消息体必须包含class、func键
        if "class" not in content or "func" not in content:
            print('[Publish Message] format error')
            return

        msg_class = content["class"]
        msg_func = content["func"]
        msg_args = content.get("args", []) or []
        msg_kwargs = content.get("kwargs", {}) or {}
        msg_special = content.get("special", "")
        msg_accepters = content.get("accepters", [])
        unique = content.get("unique", False)
        
        # 如果设置了接收者, 验证自己是否在这列表中
        if msg_accepters:
            if ACCEPTER not in map(str, msg_accepters):
                return
            if msg_func == "exec_timer":
                callback_func = msg_kwargs["callback"]
                redis_key = "%s:%s:%s" % (Message.TIMER_EVENT_KEY, callback_func, ACCEPTER)
                if redis_helper.conn.get(redis_key) != content.get("msg_id", ""):
                    return
                    
        if msg_special:
            # 特殊的 MessageAction 处理
            getattr(MessageAction, msg_func)(*msg_args, **msg_kwargs)
            if is_timer_event:
                # 设置为已读标识
                content.update({"is_read": 1})
                redis_helper.conn.hset(Message.TIMER_EVENT_KEY, original_content, json.dumps(content))
  
            if msg_id:
                # 设置为已读标识
                content.update({"is_read": 1})
                pipeline = redis_helper.conn.pipeline()
                pipeline.set(msg_id, json.dumps(content))
                pipeline.rename(msg_id, '_'+msg_id)
                pipeline.execute()
