#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import redis
import logging
import hashlib
import traceback
import tornado.web
import tornado.ioloop
from tornado import ioloop, gen
from lxml import etree
from utils import *
from db import MongoDB
from db import RedisDB
from logger_helper import logger
from wxpy import *

logger = logging.getLogger('wxpyInterface')

TURING_BOT = TuringBot()
MONGO_OBJ = MongoDB()
REDIS_OBJ = RedisDB()
global bot

@gen.coroutine
def cur_wxpy_mode():
    wxpy_mode = REDIS_OBJ.client.get('WXPY_MODE')
    logger.info('Current mode: %s' % wxpy_mode)
    bot.self.send_msg('Current mode: %s' % wxpy_mode)

@gen.coroutine
def register_task_reminder():
    if get_wxpy_mode() != 'GAI':
        logger.info('Not GAI mode, pass the reminder')
        return
    logger.info('Search register [%s] task' % ','.join(REDIS_OBJ.client.smembers('TARGET_FRIENDS')))
    for friend_name in REDIS_OBJ.client.smembers('TARGET_FRIENDS'):
        #logger.info('Search register [%s] task' % friend_name)
        #TODO 
        cur_timestramp = time.time()
        #cur_timestramp = time.mktime(time.strptime('2018-04-07 11:52:00','%Y-%m-%d %H:%M:%S'))
        remind_info = MONGO_OBJ.task_reminder(friend_name, cur_timestramp, duration=REMIND_DURATION)
        friend = bot.friends().search(friend_name)[0] if bot.friends().search(friend_name) else None
        if remind_info.strip() and friend:
            bot.self.send_msg('Send remind to [%s] [%s]' % (friend_name, remind_info.strip()))
            #TODO add friend reminder
            friend.send_msg(remind_info.strip() + '\n' + TARGET_SUFFIX)
            
def set_wxpy_mode(mode):
    REDIS_OBJ.client.set('WXPY_MODE', mode)

def get_wxpy_mode():
    return REDIS_OBJ.client.get('WXPY_MODE')

def is_target_group(cur_group_name):
    return cur_group_name in TARGET_GROUPS

def is_target_keyword(content):
    r = [k for k in TARGET_KEYWORDS if k in content]  
    return len(r) == len(TARGET_KEYWORDS)


class WxpyHandler(tornado.web.RequestHandler):
    """
    wxpy interface
    """
    #类变量
    global bot
    bot = Bot(console_qr=1, cache_path=True)
    bot.enable_puid('wxpy_puid.pkl')
    #加自己为好友
    bot.self.add()
    bot.self.accept()
    def prepare(self):
        """
        overwrite setup
        """
        logger.info('===== WXPY MESSAGE START =====')
        #清理数据库
        logger.info('Database preprocess...')
        REDIS_OBJ.client.delete('TARGET_FRIENDS')
        #TODO, 临时策略
        REDIS_OBJ.client.sadd('TARGET_FRIENDS', u'刘兵')
        REDIS_OBJ.client.sadd('TARGET_FRIENDS', u'momowa')
        MONGO_OBJ.xhx_task.remove()
        MONGO_OBJ.load_schedule(PROJ_SCHEDULE_FILE)
        MONGO_OBJ.tel_book.remove()
        MONGO_OBJ.load_tel_book(TEL_BOOK_FILE)

    def on_finish(self):
        """
        overwrite teardown
        """
        logger.info('===== WXPY MESSAGE END =====\n')
   

    @bot.register(bot.self, except_self=False)
    def self_reply(msg):
        #文本消息
        if msg.type == 'Text':
            logger.info('Receive self text msg [%s][%s][%s][%s][%s]' % (msg.text, msg.type, msg.sender, msg.receiver,
                msg.sender.puid))
            content = msg.text
            return_msg = ''
            #发送者为本人，进入控制逻辑
            content = content.strip().lower()
            if content in [u'人工', u'人工模式', u'H', u'h']:
                logger.info(u'Change mode to [%s]' % content)
                set_wxpy_mode('HUMAN') 
                logger.info(u'Current mode is [%s]' % get_wxpy_mode())
                return_msg = u'Current mode is [%s]' % get_wxpy_mode()
            elif content in [u'机器', u'机器模式', u'A', u'a']:
                logger.info(u'Change mode to [%s]' % content)
                set_wxpy_mode('AI') 
                logger.info(u'Current mode is [%s]' % get_wxpy_mode())
                return_msg = u'Current mode is [%s]' % get_wxpy_mode()
            elif content in [u'群机器', u'群机器模式', u'GA', u'ga']:
                logger.info(u'Change mode to [%s]' % content)
                set_wxpy_mode('GAI') 
                logger.info(u'Current mode is [%s]' % get_wxpy_mode())
                return_msg = u'Current mode is [%s]' % get_wxpy_mode()
            elif content in [u'?', u'stat', u'状态']:
                return_msg = 'Mode: %s\nMEM: %s' % (get_wxpy_mode(), 'TODO')
            elif content.startswith('add') or content.startswith('del'):
                #register_name
                register_names = content.strip().split()[1:] if len(content.strip().split()) > 1 else []
                if content.startswith('add'): 
                    for rn in register_names:
                        logger.info('Add register [%s]' % rn)
                        if rn == u'刘兵':
                            REDIS_OBJ.client.sadd('TARGET_FRIENDS', rn)
                            continue
                        friends = bot.friends().search(rn)
                        if len(friends) != 1:
                            logger.info('Add register failed [%s]' % ','.join(f.name for f in friends))
                            msg.forward(bot.self, prefix='Add register [%s] failed' % rn, suffix='0 or more than 1 friends found')
                            continue
                        logger.info('Add register [%s][nick_name:%s, puid=%s] success' % (rn, friends[0].nick_name, friends[0].puid))
                        REDIS_OBJ.client.sadd('TARGET_FRIENDS', rn)
                        bot.self.send_msg('Add register [%s][nick_name:%s, puid=%s] success' % (rn, friends[0].nick_name,
                            friends[0].puid))
                    logger.info(dump_json('All registers', list(REDIS_OBJ.client.smembers('TARGET_FRIENDS'))))
                    return_msg = 'All registers : [%s]'  % ','.join(list(REDIS_OBJ.client.smembers('TARGET_FRIENDS')))
                elif content == 'del':
                    #无后续参数，删除全部register
                    logger.info('Delete all registers')
                    bot.self.send_msg('Delete all registers [%s]' %
                                ','.join(list(REDIS_OBJ.client.smembers('TARGET_FRIENDS'))))
                    REDIS_OBJ.client.delete('TARGET_FRIENDS')
            elif content.strip().lower().startswith('task'):
                task_owners = content.strip().split()[1:]
                if len(task_owners) < 1:
                    logger.error('No task owner found')
                for task_owner in task_owners:
                    bot.self.send_msg(MONGO_OBJ.get_task_by_name(task_owner))
            elif content.strip().lower().startswith('tel'):
                tel_keys = content.strip().split()[1:]
                if len(tel_keys) < 1:
                    logger.error('Not found')
                for tel_key in tel_keys:
                    bot.self.send_msg(MONGO_OBJ.get_tel_info_by_key(tel_key))
            #return时return_msg将发送到自己微信
            return return_msg
        #文件消息
        elif msg.type == 'Attachment':
            logger.info('Receive self file msg [%s][%s][%s][%s][%s]' % (msg.file_name, msg.type, msg.sender, msg.receiver,
                msg.sender.puid))
            if msg.file_name == os.path.split(PROJ_SCHEDULE_FILE)[1]:
                msg.get_file(save_path=PROJ_SCHEDULE_FILE)
                logger.info('Save received file %s to %s' % (msg.file_name, PROJ_SCHEDULE_FILE))
                MONGO_OBJ.xhx_task.remove()
                cnt = MONGO_OBJ.load_schedule(PROJ_SCHEDULE_FILE)
                bot.self.send_msg('%s tasks loaded' % cnt)
            elif msg.file_name == os.path.split(TEL_BOOK_FILE)[1]:
                msg.get_file(save_path=TEL_BOOK_FILE)
                logger.info('Save received file %s to %s' % (msg.file_name, TEL_BOOK_FILE))
                MONGO_OBJ.tel_book.remove()
                cnt = MONGO_OBJ.load_tel_book(TEL_BOOK_FILE)
                bot.self.send_msg('%s tel loaded' % cnt)



    @bot.register(Friend, TEXT)
    def friend_reply(msg):
        logger.info('Receive friend msg [%s] from [%s][%s] to [%s][%s]' % (msg.text, msg.sender, msg.sender.puid, msg.receiver,
            msg.receiver.puid))
        msg.forward(bot.self, prefix='Receive friend msg [', suffix='] from %s' % msg.sender.name)
        if msg.text.strip() in [u'?', u'？']:
            msg.sender.send_msg(u'【WARNING】\n本功能仅适用于826工程投产演练及上线流程，非法使用带来的生理或心理伤害，本人概不负责:)\n\n【当前功能】\n1. 回复“task 姓名”, 获取名下所有责任人和复核人任务\n2. 回复“add 姓名”，经本人注册后，可接收任务提醒（开始前10分钟，指令群@时，结束前10分钟，暂无法区分高威与单高威）\n3. 回复“tel 姓名”，查询目标姓名的联系方式\n\nPS: 自建乞丐服务器，CPU low，存储low，网络low，随时存在宕机风险，且用且珍惜！欢迎提bug，反正提了也不改\n祝各位826一切顺利！' + TARGET_SUFFIX) 
        elif msg.text.strip().lower().startswith('task'):
            task_owners = msg.text.strip().split()[1:]
            if len(task_owners) < 1:
                logger.error('No task owner found')
            for task_owner in task_owners:
                msg.sender.send_msg(MONGO_OBJ.get_task_by_name(task_owner))
        elif msg.text.strip().lower().startswith('tel'):
            tel_keys = msg.text.strip().split()[1:]
            if len(tel_keys) < 1:
                logger.error('Not found')
            for tel_key in tel_keys:
                msg.sender.send_msg(MONGO_OBJ.get_tel_info_by_key(tel_key))
        
    @bot.register(Group, TEXT)
    def group_reply(msg):
        #logger.info('msg : [%s] [%s] [%s]', type(msg), dump_json('debug', dir(msg)), dump_json('raw', msg.raw))
        #logger.info('Receive group msg [%s] from [%s][%s] to [%s][%s] in group[%s][%s]' % (msg.text, msg.member, msg.member.puid, msg.receiver,
        #    msg.receiver.puid, msg.chat.nick_name, msg.chat.puid))
        if get_wxpy_mode() == 'GAI' and is_target_group(msg.chat.nick_name) and is_target_keyword(msg.text):
            logger.info('Receive target group msg [%s] from [%s][%s] to [%s][%s] in group[%s][%s]' % (msg.text, msg.member, msg.member.puid, msg.receiver, msg.receiver.puid, msg.chat.nick_name, msg.chat.puid))
            #check @TARGET_FRIENDS or not
            target_group = bot.groups().search(msg.chat.nick_name)[0] if bot.groups().search(msg.chat.nick_name) else None
            if not target_group:
                logger.error('Target group not found : [%s]' % msg.chat.nick_name)
                return
            #更新目标群member信息
            #target_group.update_group(members_details=True)
            for friend_name in REDIS_OBJ.client.smembers('TARGET_FRIENDS'):
                friends = bot.friends().search(friend_name)
                if friend_name not in msg.text or len(friends) != 1:
                    logger.debug('Found zero or more than one friend [%s] [%s]' % (friend_name, ','.join([f.name for f in friends])))
                    continue
                logger.info('Display name [%s] -> [%s]' % (friend_name, msg.chat.search(friend_name)[0].display_name))
                #if ('@' + friend[0].display_name) in msg.text:
                if friend_name in msg.text:
                    log_info = 'Send notice [%s] to register [%s]' % (msg.text, friends[0].name)
                    logger.info(log_info)
                    msg.forward(friends[0], suffix=TARGET_SUFFIX)
                    msg.forward(bot.self, prefix='Send notice [', suffix='] to register %s' % friends[0].name)
            if msg.is_at:
                time.sleep(10)
                logger.info('Send auto reply [%s] in group [%s]' % (TARGET_REPLY, msg.chat.nick_name))
                msg.reply_msg(TARGET_REPLY)
                msg.forward(bot.self, prefix='Send auto reply [', suffix='in group [%s]' % msg.chat.nick_name)
                msg.forward(bot.friends().search(u'李春春')[0], suffix=TARGET_SUFFIX)



if __name__ == "__main__":
    pass
