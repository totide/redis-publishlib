# -*- coding: utf-8 -*-

import time
import threading
import uuid
import json
import traceback
import redis

import conf


class RedisHelper(object):
    """
        Implementation of timers, messages
    """
    EXPIRED_CHANNELS = ['__keyevent@%d__:expired' % num for num in range(16)]
    TIMER_EVENT_KEY = "timer_event"

    def __init__(self):
        self.host = conf.HOST
        self.port = conf.PORT
        self.password = conf.PASSWORD

        self.conn = self.get_conn()
        # 定义订阅频道名称
        self.channel = 'cross_server'                    

    def publish(self, msg, channel="", json_str=False):
        """Publish channel messaging

        :param msg: message content or message id
        :param channel: channel name
        :param json_str: msg'format
        :return: bool
        """
        if not json_str:
            msg = json.dumps({"__id__": msg})
            
        num = self.conn.publish(channel or self.channel, msg)
        return bool(num)

    def subscribe(self, channels=[]):  # 定义订阅方法
        """Subscribe channel

        :param channels: channel name list
        :return:
        """
        pub = self.conn.pubsub()
        if not channels:
            channels = [self.channel]
            
        pub.subscribe(*channels)
        pub.parse_response()
        return pub

    def get_conn(self):
        if self.password:
            conn = redis.Redis(host=self.host, port=self.port, password=self.password)
        else:
            conn = redis.Redis(host=self.host, port=self.port)

        return conn

    def save_msg(self, msg_info, expire_time=None, prefix=""):
        """Store message data into redis

        :param msg_info: content can be serialized by JSON
        :param expire_time: unit is seconds
        :param prefix: message ID prefix is easy to categorize

        :return:
        """
        msg_id = uuid.uuid4().hex
        if prefix:
            msg_id = "%s_%s" % (prefix, msg_id)
        if expire_time:
            self.conn.setex(msg_id, json.dumps(msg_info), expire_time)
        else:
            self.conn.set(msg_id, json.dumps(msg_info))
        return msg_id

    def create_timer_event(self, msg_info, expire_time=0, expire_sec=0, prefix=""):
        """Create timer based on key expiration time

        :param msg_info: content can be serialized by JSON, type is dict
        :param expire_time: unix timestamp
        :param expire_sec: unit is seconds
        :param prefix: message ID prefix is easy to categorize
        :return:
        """
        msg_id = uuid.uuid4().hex
        now = int(time.time())
        if prefix:
            msg_id = "%s_%s" % (prefix, msg_id)

        # 计算失效秒数
        if expire_time and expire_time > now:
            expire_sec = expire_time - now
            msg_info['expire_time'] = expire_time
        else:
            if expire_sec <= 0:
                expire_sec = 1
            msg_info['expire_time'] = now + expire_sec

        # unique: 全局定时器惟一标识
        # callback: redis键失效时触发该方法
        # accepters: 哪些可以接收该定时器的调用
        unique = msg_info.get("unique", False)
        callback_func = msg_info['kwargs']["callback"]
        accepters = msg_info.get("accepters", [])
        msg_info['msg_id'] = msg_id
        msg_info['create_time'] = now

        # save timer keys
        msg_info = json.dumps(msg_info)
        pipeline = self.conn.pipeline()
        pipeline.hset(RedisHelper.TIMER_EVENT_KEY, msg_id, msg_info)
        pipeline.setex(msg_id, msg_info, int(expire_sec))

        # 全局定时器覆盖旧的数据
        if unique:
            for accepter in accepters:
                pipeline.set("%s:%s:%s" % (RedisHelper.TIMER_EVENT_KEY, callback_func, accepter), msg_id)
            if not accepters:
                pipeline.set("%s:%s" % (RedisHelper.TIMER_EVENT_KEY, callback_func), msg_id)
        pipeline.execute()

        return msg_id

    def cancel_timer_event(self, timer_id):
        """Cancel timer by timer id

        """
        pipeline = self.conn.pipeline()
        pipeline.hdel(RedisHelper.TIMER_EVENT_KEY, timer_id)
        pipeline.delete(timer_id)
        pipeline.execute()

    def keep_alive(self):
        """Keep client long connection

        """
        _thread = threading.Thread(target=self._ping)
        _thread.start()

    def _ping(self, seconds=60):
        """Ping redis server per minute

        """
        while True:
            time.sleep(seconds)
            if not self.conn.ping():
                print("conn get lost. call him back now!")
                self.conn = self.get_conn()


redis_helper = RedisHelper()


