#!/usr/bin/python
#-*- coding: utf -8 -*-

import itchat
import logging
import traceback
import tornado.ioloop
from db import MongoDB, RedisDB
from tornado import ioloop, gen
from tornado.ioloop import PeriodicCallback
from logger_helper import logger
#from itchatInterface import cur_itchat_mode
from wxpyInterface import cur_wxpy_mode

logger = logging.getLogger('taskSchedule')

class TaskSchedule(object):
    def __init__(self):
        #self.mdb = MongoDB()
        self.rdb = RedisDB()
        self.duration = 2000

    def execute(self):
        logger.info('DB routine job start')
        tornado.ioloop.IOLoop.instance().call_later(0, self.query)
        tornado.ioloop.PeriodicCallback(self.query, self.duration).start()
        tornado.ioloop.IOLoop.current().start()
    
    def redisSchedule(self, duration=2000):
        #ioloop.PeriodicCallback(cur_wxpy_mode, duration).start()
        #ioloop.IOLoop.current().start()
        logger.info('redis routine job start')
        tornado.ioloop.IOLoop.instance().call_later(0, cur_wxpy_mode)
        tornado.ioloop.PeriodicCallback(cur_wxpy_mode, duration).start()
        #tornado.ioloop.IOLoop.current().start()

    def query(self):
        for i in self.db.collection.find({'MsgType': 'image', 'MsgId': '6366209871842252283'}):
            print i


if __name__ == '__main__':
    ds = DbSchedule()
    ds.execute()
    #PeriodicCallback(ds.query, 10).start()

