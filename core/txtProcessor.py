# -*- coding: utf-8 -*-

import re
import json
import copy
import logging
import requests
import traceback
from utils import *
from weixinInterface import MessageProcessor
from logger_helper import logger

logger = logging.getLogger('txtProcessor')


class TxtProcessor(MessageProcessor):
    """
    text message processor
    """
    def __init__(self, msg):
        MessageProcessor.__init__(self)
        self.msg_dic = copy.deepcopy(msg.msg_dic)
        if msg.get_msg_type() == 'text':
            self.text = msg.get_content()
        elif msg.get_msg_type() == 'voice': # 语音识别结果，UTF8编码，需要在开发者中心打开开关
            self.text = msg.get_recognition()
        self.turing_bot = TuringBot()

    def txt_process(self):
        txt_rst_str = get_random_err_msg()
        try:
            logger.info('txt_process = %s', self.text)
            if self.text in [u'刘雨墨', u'刘雨墨墨娃']:
                logger.info('Call Menu %s', SITE_IMG_URL)
                txt_rst_str = u'<a href="%s">干嘛</a>' % SITE_IMG_URL
            else:
                turing_result = self.turing_bot.get_turing_result(self.text)
                logger.info('turing_result = %s', turing_result)
                turing_json = json.loads(turing_result)
                text_strs = []
                text_strs.append(turing_json.get('text'))
                for each in turing_json.get('list', []):
                    text_strs.append(u'<a href="%s">%s</a>' % \
                                     ((each.get('detailurl', '')),
                                     each.get('article', '')))
                txt_rst_str = '\n'.join(text_strs)
        except:
            logger.error('txt_process exception = %s', traceback.format_exc())
            txt_rst_str = get_random_err_msg()
        finally:
            self.msg_dic.update({'ResponseMsg': txt_rst_str})
            logger.info('Write txt message to DB %s', \
                    json.dumps(self.msg_dic, ensure_ascii=False))
            self.insert_msg(self.msg_dic)
            return txt_rst_str



if __name__ == '__main__':
    tp = TxtProcessor(u'你几岁了')
    tp.txt_process()
