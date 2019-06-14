# -*- coding: utf-8 -*-

import traceback
import threading

from helper import redis_helper
from protocol import Message


def parse_response(server_id="", sdk_type=""):
    redis_helper.keep_alive()
    main_channel = "%s_%s" % (sdk_type, server_id)
    channels = [redis_helper.channel, '__keyevent@0__:expired', main_channel]
    redis_sub = redis_helper.subscribe(channels)

    def _parse_response():

        while True:
            msg = redis_sub.parse_response(block=False, timeout=60)
            if msg:
                try:
                    Message.read(*msg)
                except Exception as e:
                    print traceback.print_exc()

    _thread = threading.Thread(target=_parse_response)
    _thread.start()

    return _thread
