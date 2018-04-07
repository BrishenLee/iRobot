# -*- coding: utf-8 -*-

import re
import json
import redis
import logging
import requests
import traceback
from utils import *
from functools import wraps
from pymongo import MongoClient
from logger_helper import logger

logger = logging.getLogger('db')


def singleton(cls):
    instances = {}
    @wraps(cls)
    def getinstance(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return getinstance

@singleton
class MongoDB(object):
    def __init__(self):
        self.client = MongoClient()
        #创建weixin数据库
        self.db = self.client.weixin
        #创建weixin_msg表
        self.collection = self.db.weixin_msg

    def parse_item(self, k, with_id=False):
        """
        strip _id by default
        """
        pass
    
    def insert_msg(self, msg_dic):
        self.collection.insert_one(msg_dic)

    def search_msg(self, msg_dic):
        return self.collection.find(msg_dic)


@singleton
class RedisDB(object):
    def __init__(self):
        #self.client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
        self.client = redis.Redis(connection_pool=pool)

    def get(self, k):
        return self.client.get(k)


if __name__ == '__main__':
    #mdb = MongoDB()
    #mdb.collection.insert_one({'test': 1})
    #for i in mdb.collection.find({'MsgType': 'image'}):
    #    print i, type(i)
    rdb = RedisDB()
    rdb.client.set('test_key', 'test_value')
    print rdb.client.get('test_key')
    print rdb.client.get('no_key')
    rdb.client.sadd('test_key1', 'aa', 'bb')
    rdb.client.sadd('test_key1', 'aa', 'bb')
    rdb.client.sadd('test_key1', 'cc')
    print rdb.client.scard('test_key1')
    print rdb.client.smembers('test_key1')
    rdb.client.sadd('TARGET_FRIENDS', 'liubingnlp', 'L18656569610', 'wmm_hfut', 'oukayi', 'lichunchun_120')
    for r in rdb.client.smembers('TARGET_FRIENDS'):
        print r
