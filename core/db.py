# -*- coding: utf-8 -*-

import re
import time
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
        #TODO 临时策略for xhx，创建xhx_task表
        self.xhx_task = self.db.xhx_task

    def parse_item(self, k, with_id=False):
        """
        strip _id by default
        """
        pass
    
    def insert_msg(self, msg_dic):
        self.collection.insert_one(msg_dic)

    def search_msg(self, msg_dic):
        return self.collection.find(msg_dic)

    def load_schedule(self, schedule_file):
        logger.info('Loading schedule file %s' % schedule_file)
        cnt = 0
        for line in open(schedule_file):
            if line and line.strip().startswith('ZK') and len(line.strip().split('\t')) == 6:
                task_id, task_desc, task_owner, task_checker, task_beg_time, task_end_time = line.strip().split('\t')[:6]
                try:
                    task_beg_timestramp = time.mktime(time.strptime(task_beg_time,'%Y-%m-%d %H:%M:%S'))
                    task_end_timestramp = time.mktime(time.strptime(task_end_time,'%Y-%m-%d %H:%M:%S'))
                except:
                    logger.error('Error time format in task %s' % task_id)
                    continue
                task_dic = {"task_id": task_id, 
                        "task_desc": task_desc, 
                        "task_owner": task_owner,
                        "task_checker":task_checker,
                        "task_beg_time":task_beg_time,
                        "task_end_time":task_end_time,
                        "task_beg_timestramp":task_beg_timestramp,
                        "task_end_timestramp":task_end_timestramp,
                        "task_raw_str":line.strip(),
                        "is_noticed":0}
                cnt += 1
                if cnt % 100 == 0:
                    logger.info('%s tasks loaded' % cnt)
                self.xhx_task.insert_one(task_dic)
        logger.info('All [%s] tasks loaded' % cnt)
        for t in self.xhx_task.find({'task_owner': u"刘兵"}):
            logger.info(t)
        return cnt

    def get_task_by_name(self, name):
        logger.info('Search mongodb by %s' % name)
        task_infos = []
        for it,t in enumerate(self.xhx_task.find({"$or":[{"task_owner":name},
            {"task_checker":name}]}).sort("time_beg_timestramp")):
            logger.info(t)
            task_info = []
            task_info.append(u'【Task %s】' % (it+1))
            task_info.append(u'任务书编号: %s' % t.get('task_id'))
            task_info.append(u'任务书描述: %s' % t.get('task_desc'))
            task_info.append(u'负责人: %s' % t.get('task_owner'))
            task_info.append(u'监督人: %s' % t.get('task_checker'))
            task_info.append(u'计划开始时间: %s' % t.get('task_beg_time'))
            task_info.append(u'计划结束时间: %s\n' % t.get('task_end_time'))
            task_infos.append('\n'.join(task_info))
        return '\n'.join(task_infos) if task_infos else 'No task found'

    def task_reminder(self, name, cur_timestramp, duration=600):
        #logger.info('beg_task_noticer %s %s' % (name, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cur_timestramp))))
        notice_infos = ''
        for it,t in enumerate(self.xhx_task.find({"$or":[{"task_owner":name},
            {"task_checker":name}]}).sort("time_beg_timestramp")):
            notice_info = []
            task_id = t.get('task_id')
            task_desc = t.get('task_desc')
            beg_time = t.get('task_beg_time', 0)
            end_time = t.get('task_end_time', 0)
            beg_timestramp = t.get('task_beg_timestramp', 0)
            end_timestramp = t.get('task_end_timestramp', 0)
            notice_flag = t.get('is_noticed', 0)
            if notice_flag == 1 or beg_timestramp == 0 or end_timestramp == 0:
                continue
            #任务即将开始
            if cur_timestramp > beg_timestramp - duration:
                notice_info.append(u'任务[%s]%s将于%s开始，请注意签收并回复指令！' % (task_id, task_desc, beg_time))
                self.xhx_task.update({"task_id":task_id}, {"$set":{"is_noticed":1}})
            elif cur_timestramp > end_timestramp - duration:
                notice_info.append(u'任务[%s]%s将于%s结束，请注意修改任务状态！' % (task_id, task_desc, end_time))
                self.xhx_task.update({"task_id":task_id}, {"$set":{"is_noticed":1}})
            notice_infos += '\n'.join(notice_info)
        return notice_infos.strip()
        
         

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
