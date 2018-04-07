#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import redis
import itchat
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
from itchat.content import *

logger = logging.getLogger('itchatInterface')

TURING_BOT = TuringBot()
MONGO_OBJ = MongoDB()
REDIS_OBJ = RedisDB()


@gen.coroutine
def cur_itchat_mode():
    itchat_mode = REDIS_OBJ.client.get('ITCHAT_MODE')
    logger.info('Current mode: %s' % itchat_mode)
    #itchat.send_msg('Current mode: %s' % itchat_mode)

def set_itchat_mode(mode):
    REDIS_OBJ.client.set('ITCHAT_MODE', mode)

def get_itchat_mode():
    return REDIS_OBJ.client.get('ITCHAT_MODE')

def is_target_chatroom(cur_chatroom_id):
    target_chatrooms = itchat.search_chatrooms(TARGET_CHATROOM)
    logger.debug(dump_json('target_chatrooms', target_chatrooms))
    if target_chatrooms and target_chatrooms[0].get('UserName') == cur_chatroom_id:
        return True
    return False

def is_target_keyword(content):
    r = [k for k in TARGET_KEYWORDS if k in content]  
    return len(r) == len(TARGET_KEYWORDS)


class ItChatHandler(tornado.web.RequestHandler):
    """
    itchat interface
    """
    def prepare(self):
        """
        overwrite setup
        """
        logger.info('===== ITCHAT MESSAGE START =====')
        itchat.auto_login(hotReload=True, enableCmdQR=True)
        itchat.run()
        #获取friends和chatroom信息
        logger.debug('Friend list :' + json.dumps(itchat.get_friends(update=True), indent=True, ensure_ascii=False))
        logger.debug('Chatroom list :' + json.dumps(itchat.get_chatrooms(update=True), indent=True, ensure_ascii=False))

    def on_finish(self):
        """
        overwrite teardown
        """
        logger.info('===== ITCHAT MESSAGE END =====\n')
    
   
    @itchat.msg_register(TEXT, isGroupChat=True)
    def group_reply(msg):
        #global ITCHAT_MODE
        logger.debug(dump_json(u'group dict', msg))
        chatroom_id = msg.get('FromUserName')
        #chatroom_name = msg.get('User').get('NickName') if msg.get('User') else 'SomeGroup'
        chatroom_name = itchat.search_chatrooms(chatroom_id).get('NickName') if itchat.search_chatrooms(chatroom_id) else 'SomeGroup'
        from_user = msg.get('ActualNickName', 'Somebody')
        content = msg.get('Text')
        if msg.get('isAt'):
            msg_log_info = u'Receive message [%s] at you from [%s] in group [%s]' % (content, from_user, chatroom_id)
            msg_send_info = u'Receive message [%s] at you from [%s] in group [%s]' % (content, from_user, chatroom_name)
            logger.info(msg_log_info)
            itchat.send_msg(msg_send_info)
        else:
            msg_log_info = u'Receive message [%s] from [%s] in group [%s]' % (content, from_user, chatroom_id)
            msg_send_info = u'Receive message [%s] from [%s] in group [%s]' % (content, from_user, chatroom_name)
            logger.info(msg_log_info)
            itchat.send_msg(msg_send_info)
        itchat_mode = get_itchat_mode()
        if itchat_mode == 'GAI' and is_target_chatroom(chatroom_id) and is_target_keyword(content):
            logger.info('Get target chatroom %s' % chatroom_name)
            #for friend in REDIS_OBJ.client.smembers('TARGET_FRIENDS'):
            for friend in TARGET_FRIENDS:
                #未@到的，直接跳过 TODO 根据displayName精细判断
                if friend not in content:
                    continue
                friend_info = itchat.search_friends(name=friend)
                if friend_info:
                    itchat.send_msg(content + TURING_BOT.suffix, friend_info[0].get('UserName'))
                    itchat.send_msg('Send notice [%s] to [%s] in group [%s]' % (content, friend, chatroom_name))
            #有@自己的消息，sleep后回复
            if msg.get('isAt'):
                time.sleep(10)
                itchat.send_msg(TARGET_REPLY, toUserName=msg.get('FromUserName'))
                itchat.send_msg('Send auto reply [%s] in group [%s]' % (TARGET_REPLY, chatroom_name))

        
    
    @itchat.msg_register(TEXT, isFriendChat=True)
    def friend_reply(msg):
        #itchat control
        #global ITCHAT_MODE
        itchat_mode = get_itchat_mode()
        logger.info('ITCHAT_MODE is %s' % itchat_mode)
        logger.debug(dump_json(u'friend reply dict', msg))
        #获取当前用户nickname
        friends = itchat.search_friends()
        master_name = friends.get('NickName') 
        logger.debug(dump_json(u'search friend dict', friends))
        from_user = itchat.search_friends(userName=msg.get('FromUserName'))
        to_user = itchat.search_friends(userName=msg.get('ToUserName'))
        from_user_name = from_user.get('NickName', 'Somebody')
        content = msg.get('Text')

        msg_log_info = u'Receive message [%s] from [%s]' % (content, msg.get('FromUserName'))
        msg_send_info = u'Receive message [%s] from [%s]' % (content, from_user_name)
        logger.info(msg_log_info)
        itchat.send_msg(msg_send_info)
        #发送者为master自己，且发送给本人时，进入控制逻辑
        if (from_user_name == master_name) and (from_user == to_user):
            if content in [u'人工', u'人工模式', u'H', u'h']:
                logger.info(u'Change mode to [%s]' % content)
                set_itchat_mode('HUMAN') 
                logger.info(u'Current mode is [%s]' % get_itchat_mode())
                itchat.send_msg(u'Current mode is [%s]' % get_itchat_mode())
            elif content in [u'机器', u'机器模式', u'A', u'a']:
                logger.info(u'Change mode to [%s]' % content)
                set_itchat_mode('AI') 
                logger.info(u'Current mode is [%s]' % get_itchat_mode())
                itchat.send_msg(u'Current mode is [%s]' % get_itchat_mode())
            elif content in [u'群机器', u'群机器模式', u'GA', u'ga']:
                logger.info(u'Change mode to [%s]' % content)
                set_itchat_mode('GAI') 
                logger.info(u'Current mode is [%s]' % get_itchat_mode())
                itchat.send_msg(u'Current mode is [%s]' % get_itchat_mode())
            elif content in [u'?', u'stat', u'状态']:
                status_msg = 'Mode: %s\nMEM: %s' % (get_itchat_mode(), 'TODO')
                itchat.send_msg(status_msg)
        else:
            logger.info('ITCHAT_MODE here is %s' % get_itchat_mode())
            if get_itchat_mode() == 'AI':
                robot_send_info = TURING_BOT.get_turing_result(content)
                robot_send_info = json.loads(robot_send_info).get('text')
                default_send_info = u'主人不在服务区，现在是托管模式'
                msg_send_info = robot_send_info if robot_send_info else default_send_info
                logger.info('AI response is %s' % msg_send_info)
                itchat.send_msg(msg=msg_send_info + TURING_BOT.suffix, toUserName=msg.get('FromUserName'))
            elif get_itchat_mode() == 'GAI':
                if content == u'任务':
                    logger.info(u'Receive regisiter [%s/%s]' % (from_user_name, from_user))
                    REDIS_OBJ.client.sadd('REGISITER', from_user_name)
                    itchat.send_msg(u'Receive regisiter [%s/%s]' % (from_user_name, from_user))
        

if __name__ == "__main__":
    itchat.auto_login(hotReload=True, enableCmdQR=True)
    itchat.run()
