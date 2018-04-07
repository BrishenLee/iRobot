# -*- coding: utf-8 -*-

import os
import sys
import web
import time
import json
import urllib
import logging
import hashlib
import traceback
from lxml import etree
from utils import *

logger = logging.getLogger('weixin')
formatter = logging.Formatter(\
        '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        '%a, %d %b %Y %H:%M:%S')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


class Index():
    def GET(self):
        return "Hello world"


class WeixinInterface:
    def __init__(self):
        self.app_root = os.path.dirname(__file__)
        self.templates_root = os.path.join(self.app_root, 'templates')
        self.render = web.template.render(self.templates_root)

    def GET(self):
        #获取输入参数
        data = web.input()
        signature=data.signature
        timestamp=data.timestamp
        nonce=data.nonce
        echostr = data.echostr
        #自己的token
        token=DEV_TOKEN #这里改写你在微信公众平台里输入的token
        #字典序排序
        list=[token,timestamp,nonce]
        list.sort()
        sha1=hashlib.sha1()
        map(sha1.update,list)
        hashcode=sha1.hexdigest()
        #sha1加密算法

        #如果是来自微信的请求，则回复echostr
        if hashcode == signature:
            return echostr

    def POST(self):
        str_xml = web.data()
        xml = etree.fromstring(str_xml)
        mstype = xml.find("MsgType").text
        fromUser = xml.find("FromUserName").text
        toUser = xml.find("ToUserName").text

        logger.info('%s MSG = %s', mstype.upper(), str_xml)
        if mstype in ['text', 'voice']:
            from txtProcessor import TxtProcessor
            txt_processor = TxtProcessor(xml, mstype)
            txt_rst_str = txt_processor.txt_process()
            return self.render.reply_text(fromUser, toUser, \
                                          int(time.time()), \
                                          txt_rst_str)
        elif mstype == 'image':
            from imgProcessor import ImgProcessor
            img_processor = ImgProcessor(xml)
            img_rst_str = img_processor.img_process()
            return self.render.reply_text(fromUser, toUser, \
                                          int(time.time()), \
                                          img_rst_str)
        elif mstype == 'event':
            from evtProcessor import EvtProcessor
            evt_processor = EvtProcessor(xml)
            evt_rst_str = evt_processor.evt_process()
            return self.render.reply_text(fromUser, toUser, \
                                          int(time.time()), \
                                          evt_rst_str)
        elif mstype == 'location':
            from locProcessor import LocProcessor
            loc_processor = LocProcessor(xml)
            loc_rst_str = loc_processor.loc_process()
            return self.render.reply_text(fromUser, toUser, \
                                          int(time.time()), \
                                          loc_rst_str)
        else:
            return self.render.reply_text(fromUser, toUser, int(time.time()), \
                                          '这种消息我还不会处理，等我长大哦！')


if __name__ == '__main__':
    urls = (
    '/', 'Index',
    '/weixin', 'WeixinInterface')
    app = web.application(urls, globals())
    logger.info('SERVER START ...')
    app.run()
