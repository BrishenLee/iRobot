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
#清理数据库
REDIS_OBJ.client.delete('TARGET_FRIENDS')
global bot

@gen.coroutine
def cur_wxpy_mode():
    wxpy_mode = REDIS_OBJ.client.get('WXPY_MODE')
    logger.info('Current mode: %s' % wxpy_mode)
    bot.self.send_msg('Current mode: %s' % wxpy_mode)

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

    def on_finish(self):
        """
        overwrite teardown
        """
        logger.info('===== WXPY MESSAGE END =====\n')
   

    @bot.register(bot.self, except_self=False)
    def self_reply(msg):
        logger.info('Receive self msg [%s][%s][%s][%s][%s]' % (msg.text, msg.type, msg.sender, msg.receiver,
            msg.sender.puid))
        content = msg.text
        return_msg = ''
        #发送者为本人，进入控制逻辑
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
        elif content.strip().lower().startswith('add'):
            #add register_name
            register_names = content.strip().split()[1:] if len(content.strip().split()) > 1 else []
            for rn in register_names:
                logger.info('Add register [%s]' % rn)
                REDIS_OBJ.client.sadd('TARGET_FRIENDS', rn)
                msg.forward(bot.self, prefix='Add register')
            logger.info(dump_json('All registers', list(REDIS_OBJ.client.smembers('TARGET_FRIENDS'))))
            return_msg = 'All registers : [%s]'  % ','.join(list(REDIS_OBJ.client.smembers('TARGET_FRIENDS')))
        #return时return_msg将发送到自己微信
        return return_msg

    @bot.register(Friend, TEXT)
    def friend_reply(msg):
        logger.info('Receive friend msg [%s] from [%s][%s] to [%s][%s]' % (msg.text, msg.sender, msg.sender.puid, msg.receiver,
            msg.receiver.puid))
        msg.forward(bot.self, prefix='Receive friend msg [', suffix='] from %s' % msg.sender.name)
            
    @bot.register(Group, TEXT)
    def group_reply(msg):
        #logger.info('msg : [%s] [%s] [%s]', type(msg), dump_json('debug', dir(msg)), dump_json('raw', msg.raw))
        logger.info('Receive group msg [%s] from [%s][%s] to [%s][%s] in group[%s][%s]' % (msg.text, msg.member, msg.member.puid, msg.receiver,
            msg.receiver.puid, msg.chat.nick_name, msg.chat.puid))
        if get_wxpy_mode() == 'GAI' and is_target_group(msg.chat.nick_name) and is_target_keyword(msg.text):
            #check @TARGET_FRIENDS or not
            target_group = bot.groups().search(msg.chat.nick_name)[0] if bot.groups().search(msg.chat.nick_name) else None
            if not target_group:
                logger.error('Target group not found : [%s]' % msg.chat.nick_name)
                return
            #更新目标群member信息
            #target_group.update_group(members_details=True)
            for friend_name in REDIS_OBJ.client.smembers('TARGET_FRIENDS'):
                friends = bot.friends().search(friend_name)
                if len(friends) != 1:
                    logger.info('Found zero or more than one friend [%s] [%s]' % (friend_name, ','.join([f.name for f in friends])))
                    continue
                log_info = 'Send notice [%s] to register [%s]' % (msg.text, friends[0].name)
                logger.info(log_info)
                msg.forward(friends[0], suffix=TARGET_SUFFIX)
                msg.forward(bot.self, prefix='Send notice [', suffix='] to register %s' % friends[0].name)
            if msg.is_at:
                time.sleep(10)
                logger.info('Send auto reply [%s] in group [%s]' % (TARGET_REPLY, msg.chat.nick_name))
                msg.reply_msg(TARGET_REPLY)
                msg.forward(bot.self, prefix='Send auto reply [', suffix='in group [%s]' % msg.chat.nick_name)
                msg.forward(bot.friends.search(u'lichunchun_0120')[0], suffix=TARGET_SUFFIX)



if __name__ == "__main__":
    pass
