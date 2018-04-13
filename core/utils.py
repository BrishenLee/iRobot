# -*- coding: utf-8 -*-

import os
import json
import random
import logging
import requests
import traceback

logger = logging.getLogger('utils')

DEV_TOKEN = 'brishen'
SITE_BASE_URL = u'http://sice.hk1.mofasuidao.cn/'
SITE_IMG_URL = u'%simg' % SITE_BASE_URL
SUB_WEL_MSG = u'欢迎关注刘雨墨墨娃的个人订阅号，这里是刘雨墨家族的私家庭院，使用说明在<a href=xxx>这里</a>哦'

LOC_LABEL_NIL_MSG = u'伦家不知道你在神马地方:('
PIC_NO_REC_MSG = u'这图太抽象，真心看不懂，麻烦换一张'
WEA_NO_REC_MSG = u'龙王不在家，待会我再问问他此地还要不要下雨'

#TODO
PROJ_PATH = os.path.expanduser('~/project/weixin_local/')
#PROJ_CORE_PATH = '/home/pi/Project/weixin_local/core/'
PROJ_CORE_PATH = '%s/core' % PROJ_PATH
PROJ_LOG_FILE = '%s/log/weixin.log' % PROJ_PATH
PROJ_SCHEDULE_FILE = '%s/TASK.txt' % PROJ_CORE_PATH
WEIXIN_PIC_PATH = '%s/static/weixin_img/' % PROJ_CORE_PATH
WEIXIN_THUMBPIC_PATH = '%s/static/weixin_thumb/' % PROJ_CORE_PATH

#temp config
TARGET_GROUPS = [u'826工程投产（演练）指令群']
#TARGET_GROUPS = [u'ITCHAT-TEST']
TARGET_KEYWORDS = [u'具备执行条件', u'收到请回复']
TARGET_REPLY = u'收到'
TARGET_SUFFIX = u"--From Brishen's robot"
REMIND_DURATION = 600

def get_random_err_msg():
    rand_msgs = [u'哎呀，伦家懵逼了', \
                 u'不想回答你，我要静静', \
                 u'放学了，我要回家去']
    return random.choice(rand_msgs)


def xml_to_json(xml):
    #xml should be an etree object
    json_ret = {}
    for elem in xml.iterchildren():
        json_ret[elem.tag] = elem.text
    logger.info('xml_to_json %s', json.dumps(json_ret))
    return json_ret


def dump_json(prefix_info, msg_dic):
    return prefix_info + u' ==> ' + json.dumps(msg_dic, indent=True, ensure_ascii=False)


class TuringBot(object):
    def __init__(self):
        self.api_key = '1196eedd971d412e844693b867110ff6'
        self.api_secret = None
        self.turing_url = 'http://www.tuling123.com/openapi/api?key=%s&info=' % self.api_key
        self.suffix = u" --From Brishen's robot"

    def get_turing_result(self, query):
        """
        query should be unicode
        """
        try:
            s = requests.session()
            r = s.get(self.turing_url + query.encode('utf-8'))
            #return r.content
            return r.content.decode('utf-8')
        except:
            logger.error('call turing bot error %s' % traceback.format_exc())
            return '{}' 

