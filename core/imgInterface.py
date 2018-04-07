# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import traceback
import tornado.web
import tornado.ioloop
from utils import *
from db import MongoDB
from logger_helper import logger


class ImgHandler(tornado.web.RequestHandler):
    def prepare(self):
        """
        overwrite setup
        """
        logger.info('===== IMG MESSAGE START =====')

    def on_finish(self):
        """
        overwrite teardown
        """
        logger.info('===== IMG MESSAGE END =====\n')

    def get_rela_pic_path(self, abs_pic_path):
        """
        get relative pic path based on absolute path and PROJ_CORE_PATH
        """
        if not abs_pic_path or \
            not abs_pic_path.startswith(PROJ_CORE_PATH):
            return None
        return abs_pic_path[len(PROJ_CORE_PATH):]

    def get(self):
        db = MongoDB()
        pics = []
        #按CreateTime降序排列，最新照片在最上面，sort写法特殊，参考http://stackoverflow.com/questions/10242149/using-sort-with-pymongo
        for i in db.collection.find({'MsgType': 'image'}).sort([('CreateTime', -1)]):
            print i
            pic_path = self.get_rela_pic_path(i.get('LocalPicUrl'))
            pic_txt = i.get('ResponseMsg')
            if not pic_path or not pic_txt:
                continue
            pics.append((pic_path, pic_txt))
        self.render('img.html', pics=pics)

if __name__ == "__main__":
    db = MongoDB()
    for i in db.collection.find({'MsgType': 'image'}).sort([("CreateTime", -1)]):
        print i

