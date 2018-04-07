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

logger = logging.getLogger('locProcessor')

class WeatherReporter(object):
    def __init__(self):
        self.api_key = 'ej6kuyctadqze7nj'
        self.api_secret = 'UB64E9A036'
        self.weather_service_url = 'https://api.thinkpage.cn/v3/weather/now.json'

    def get_real_time_weather(self, longitude, latitude):
        """
        get real time weather status based on longitude and latitude
        """
        try:
            get_params = {'key': self.api_key,
                          'location': '%s:%s' % (longitude, latitude),
                          'language': 'zh-Hans',
                          'unit': 'c'}
            r = requests.get(self.weather_service_url, params=get_params)
            logger.warn('weather request = %s\n%s', json.dumps(get_params), r.content)
            weather_rst_json = json.loads(r.content)
            city_name = weather_rst_json.get('results')[0].get('location', {}).get('name')
            wea_status = weather_rst_json.get('results')[0].get('now', {}).get('text')
            wea_temp = weather_rst_json.get('results')[0].get('now', {}).get('temperature')
            return u'您所在的位置是%s，天气%s，当前温度是%s℃' % (city_name, \
                                                wea_status, wea_temp)
        except:
            logger.error(traceback.format_exc())
            return WEA_NO_REC_MSG

class LocProcessor(MessageProcessor):
    """
    location message processor
    """
    def __init__(self, msg):
        MessageProcessor.__init__(self)
        self.msg_dic = copy.deepcopy(msg.msg_dic)
        self.label = msg.get_label() 
        self.longitude = msg.get_location_x()
        self.latitude = msg.get_location_y()
        self.wea_reporter = WeatherReporter()

    def loc_process(self):
        loc_rst_str = ''
        try:
            logging.warn('loc_process = %s', self.label)
            if not self.label:
                loc_rst_str = LOC_LABEL_NIL_MSG
            else:
                loc_rst_str = self.wea_reporter.\
                        get_real_time_weather(self.longitude, self.latitude)
        except:
            logging.error(traceback.format_exc())
            loc_rst_str = get_random_err_msg()
        finally:
            self.msg_dic.update({'ResponseMsg': loc_rst_str})
            logger.info('Write loc message to DB %s', self.msg_dic)
            self.insert_msg(self.msg_dic)
            return loc_rst_str


if __name__ == '__main__':
    wr = WeatherReporter()
    wr.get_real_time_weather('31.747354', '117.296641')
