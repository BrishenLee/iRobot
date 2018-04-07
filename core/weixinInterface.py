# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import hashlib
import traceback
import tornado.web
import tornado.ioloop
from lxml import etree
from utils import *
from db import MongoDB
from logger_helper import logger

logger = logging.getLogger('weixinInterface')

class MessageProcessor(object):
    """
    message processor base class
    """
    def __init__(self):
        self.db_obj = MongoDB()
        self.msg_dic = {}

    def insert_msg(self, msg_dic):
        self.db_obj.collection.insert_one(msg_dic)

    def load_message(self, xml):
        #xml should be an etree object
        for elem in xml.iterchildren():
            self.msg_dic[elem.tag] = elem.text

    def dump_message(self):
        return json.dumps(self.msg_dic)

    def get_to_user(self):
        return self.msg_dic.get('ToUserName')

    def get_from_user(self):
        return self.msg_dic.get('FromUserName')

    def get_msg_type(self):
        return self.msg_dic.get('MsgType')

    def get_content(self):
        return self.msg_dic.get('Content')

    def get_recognition(self):
        return self.msg_dic.get('Recognition')

    def get_pic_url(self):
        return self.msg_dic.get('PicUrl')

    def get_msg_id(self):
        return self.msg_dic.get('MsgId')

    def get_label(self):
        return self.msg_dic.get('Label')

    def get_event(self):
        return self.msg_dic.get('Event')

    def get_location_x(self):
        return self.msg_dic.get('Location_X')

    def get_location_y(self):
        return self.msg_dic.get('Location_Y')


class WeixinHandler(tornado.web.RequestHandler):
    """
    微信消息处理interface
    """
    def prepare(self):
        """
        overwrite setup
        """
        logger.info('===== WEIXIN MESSAGE START =====')

    def on_finish(self):
        """
        overwrite teardown
        """
        logger.info('===== WEIXIN MESSAGE END =====\n')

    def get(self):
        signature = self.get_argument('signature')
        timestamp = self.get_argument('timestamp')
        nonce = self.get_argument('nonce')
        echostr = self.get_argument('echostr')
        check_list = [DEV_TOKEN, timestamp, nonce]
        check_list.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, check_list)
        hashcode = sha1.hexdigest()
        if hashcode == signature:
            self.write(echostr)

    def reply_text(self, from_user, to_user, create_time, content): 
        textTpl = """<xml> <ToUserName><![CDATA[%s]]></ToUserName> <FromUserName><![CDATA[%s]]></FromUserName> <CreateTime>%s</CreateTime> <MsgType><![CDATA[%s]]></MsgType> <Content><![CDATA[%s]]></Content></xml>"""
        out = textTpl % (from_user, to_user, create_time, 'text', content)
        return out

    def post(self):
        msg = MessageProcessor()
        body = self.request.body
        xml = etree.fromstring(body)
        msg.load_message(xml)

        to_user = msg.get_to_user()
        from_user = msg.get_from_user()
        msg_type = msg.get_msg_type()
        create_time = int(time.time())
        out_str = ''

        if not to_user or not from_user or not msg_type:
            logger.error('to_user/from_user/msg_type lost')
            self.write(out_str)
        logger.info('%s XML = \n%s\nMSG = %s\n', msg_type.upper(), body, msg.dump_message())
 
        if msg_type in ['text', 'voice']:
            from txtProcessor import TxtProcessor
            txt_processor = TxtProcessor(msg)
            rst_str = txt_processor.txt_process()
            out_str = self.reply_text(from_user, to_user, create_time, rst_str)
        elif msg_type == 'image':
            from imgProcessor import ImgProcessor
            img_processor = ImgProcessor(msg)
            rst_str = img_processor.img_process()
            out_str = self.reply_text(from_user, to_user, create_time, rst_str)
        elif msg_type == 'event':
            from evtProcessor import EvtProcessor
            evt_processor = EvtProcessor(msg)
            rst_str = evt_processor.evt_process()
            out_str = self.reply_text(from_user, to_user, create_time, rst_str)
        elif msg_type == 'location':
            from locProcessor import LocProcessor
            loc_processor = LocProcessor(msg)
            rst_str = loc_processor.loc_process()
            out_str = self.reply_text(from_user, to_user, create_time, rst_str)
        else:
            out_str = self.reply_text(from_user, to_user, create_time, \
                                          u'这种消息我还不会处理，等我长大哦！')
        self.write(out_str)

if __name__ == "__main__":
    pass

