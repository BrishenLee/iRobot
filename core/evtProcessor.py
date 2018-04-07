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

logger = logging.getLogger('evtProcessor')

class EvtProcessor(MessageProcessor):
    """
    event message processor
    """
    def __init__(self, msg):
        MessageProcessor.__init__(self)
        self.msg_dic = copy.deepcopy(msg.msg_dic)
        self.event = msg.get_event()

    def evt_process(self):
        evt_rst_str = ''
        try:
            logger.info('evt_process = %s', self.event)
            if self.event == 'subscribe':
                evt_rst_str = SUB_WEL_MSG
        except:
            logger.error('evt_process exception = %s', traceback.format_exc())
            evt_rst_str = get_random_err_msg()
        finally:
            self.msg_dic.update({'ResponseMsg': evt_rst_str})
            logger.info('Write evt message to DB %s', self.msg_dic)
            self.insert_msg(self.msg_dic)
            return evt_rst_str


if __name__ == '__main__':
    pass
