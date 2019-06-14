# redis-publishlib
基于redis自身特性实现定时消息与订阅消息


修改redis配置文件 /etc/redis.conf，去掉以下语句的注释，保存并退出
notify-keyspace-events Ex



1. 下载该文件目录 redis_publishlib
2. 把代码放到自己的工程根目录下
3. 修改目录下的 conf.py文件，修改redis连接地址
4. 代码中加入以下两行代码，就可以使用订阅消息、定时器消息

  from redis_publishlib import parse_response
  
  parse_response()
5. 以后需要增加协议，就可以在action.py中像 exec_timer方法一样，添加
6. 例子: 

创建定时器
   msg_info = {"special": "1", "class": "", "func": "exec_timer", "args": [],
               "kwargs": {"callback": "destroy_cross_server_data"}, "unique": True,
               "accepters": []}
   week = int(time.strftime("%w"))
   zero_timestamp = time.mktime(date.today().timetuple())
   effect_timestamp = zero_timestamp + (7 - week + 1) * 86400 + 4 * 3600 + 10 * 60
   redis_helper.create_timer_event(msg_info, expire_time=effect_timestamp)
   
删除道具
   msg_info = {"special": "1", "class": "", "func": "delete_items", "args": [角色ID, [[道具ID, 道具数量]]],
               "kwargs": {}}
   msg_id = redis_helper.save_msg(msg_info)
   redis_helper.publish(msg_id, channel="%s_%s" % ("", game_id))
   
   
协议中的 "destroy_cross_server_data"、"delete_items" 在action.py里面实现静态类方法为这两个名称就OK了
