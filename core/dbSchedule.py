#!/usr/bin/python
#-*- coding: utf -8 -*-

import logging
import traceback
import tornado.ioloop
from db import MongoDB
from tornado.ioloop import PeriodicCallback
from logger_helper import logger

logger = logging.getLogger('dbSchedule')

class DbSchedule(object):
    def __init__(self):
        self.db = MongoDB()
        self.duration = 2000

    def execute(self):
        logger.info('DB routine job start')
        tornado.ioloop.IOLoop.instance().call_later(0, self.query)
        tornado.ioloop.PeriodicCallback(self.query, self.duration).start()
        tornado.ioloop.IOLoop.current().start()

    def query(self):
        for i in self.db.collection.find({'MsgType': 'image', 'MsgId': '6366209871842252283'}):
            print i


if __name__ == '__main__':
    ds = DbSchedule()
    ds.execute()
    #PeriodicCallback(ds.query, 10).start()

