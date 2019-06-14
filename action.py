# -*- coding: utf-8 -*-

import sys


class BaseMessageAction(object):
    def __init__(self):
        super(BaseMessageAction, self).__init__()
    
    @staticmethod
    def exec_timer(*args, **kwargs):
        """
        let:
            redis_helper.create_timer_event({"special": "1", "class": "", "func": "exec_timer",
                                             "args": ["nihao"], "kwargs": {"callback": "transfer_guild_war_ranking"}})

            redis_helper.create_timer_event({"special": "1", "class": "", "func": "exec_timer",
                                             "args": ["nihao"], "kwargs": {"callback": "transfer_guild_war_ranking"}}, expire_sec=10)

            redis_helper.create_timer_event({"special": "1", "class": "", "func": "exec_timer",
                                             "args": ["nihao"], "kwargs": {"callback": "transfer_guild_war_ranking"}}, expire_time=time.time() + 30)
        :param args:
        :param kwargs:
        :return:
        """
        if "callback" not in kwargs:
            return
        if "." not in kwargs["callback"]:
            return

        import_module, import_cls, import_func = kwargs["callback"].rsplit('.', 2)
        __import__(import_module)
        import_cls = getattr(sys.modules[import_module], import_cls)
        getattr(import_cls, import_func)(*args, **kwargs)


class MessageAction(BaseMessageAction):
    @staticmethod
    def exec_timer(*args, **kwargs):
        if "callback" not in kwargs:
            return
        if "." in kwargs["callback"]:
            BaseMessageAction.exec_timer(*args, **kwargs)
        else:
            if not hasattr(MessageAction, kwargs["callback"]):
                return
            getattr(MessageAction, kwargs["callback"])(*args, **kwargs)
