# -*- coding: utf-8 -*-

import re
import json
import random
import hashlib
import logging
import requests
import traceback


class TransProcessor(object):
    """
    Baidu fanyi API
    """
    def __init__(self):
        self.fanyi_url = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
        self.api_key = '20161201000033253'
        self.api_secret = 'xgZWOyc385EsXrYZMX7u'

    def translate(self, query):
        try:
            salt = random.randint(32768, 65536)
            sign = hashlib.md5('%s%s%s%s' % \
                   (self.api_key, \
                    query, \
                    salt, \
                    self.api_secret)).hexdigest()
            logging.warn('Baidu fanyi query = %s', query)
            s = requests.session()
            post_params = {'q': query,
                           'from': 'auto',
                           'to': 'zh',
                           'appid': self.api_key,
                           'salt': salt,
                           'sign': sign}

            r = s.post(self.fanyi_url, data=post_params)
            fanyi_result = r.content
            logging.warn('Baidu fanyi result = %s', fanyi_result)
            return fanyi_result
        except:
            return {}

    def get_trans(self, query):
        """
        get single query translations
        :param query:
        :return:
        """
        try:
            trans_rst = self.translate(query)
            trans_rst_json = json.loads(trans_rst)
            #TODO get first result
            return trans_rst_json.get('trans_result')[0].get('dst', '')
        except:
            return ''


if __name__ == '__main__':
    tp = TransProcessor()
    tp.translate('apple\nOrange')
    tp.get_trans('Bank')
