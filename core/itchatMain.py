#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import itchat
import logging
import hashlib
import traceback
import tornado.web
import tornado.ioloop
from lxml import etree
from utils import *
from db import MongoDB
from logger_helper import logger
from itchat.content import *

logger = logging.getLogger('itchatMain')


@itchat.msg_register(TEXT, isFriendChat=True, isGroupChat=True)
def text_reply(self, msg):
    logger.debug(u'msg dict : ' + json.dumps(msg, indent=True, ensure_ascii=False))
    #from_user = itchat.search_friends(userName=msg['FromUserName'])['NickName'] if \
    #    itchat.search_friends(userName=msg['FromUserName']) else 'Somebody'
    from_user = msg.get('ActualNickName', 'Somebody')
    logger.info(u'Receive message [%s] from [%s]' % (msg['Text'], from_user))
    #itchat.send_msg(u'自动回复收到-来自Brishen的机器人', toUserName=msg['FromUserName'])
    if msg.get('isAt'):
        logger.info(u'收到At你的消息，内容是[%s]' % msg.get('Text'))
        itchat.send_msg(u'自动回复收到-来自Brishen的机器人', toUserName=msg.get('FromUserName'))



if __name__ == "__main__":
    itchat.auto_login(hotReload=True, enableCmdQR=True)
    itchat.run()
