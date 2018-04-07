# -*- coding: utf-8 -*-

import re
import json
import copy
import logging
import requests
import traceback
from utils import *
from transProcessor import TransProcessor
from weixinInterface import MessageProcessor
from logger_helper import logger

logger = logging.getLogger('imgProcessor')
TRANS_OBJ = TransProcessor()

class FacePlusPlus(object):
    """
    funcs provided by face++
    """
    def __init__(self, picurl):
        self.picurl = picurl
        self.local_pic_path = None
        self.local_thumb_path = None
        self.face_detect_url = 'https://api.megvii.com/facepp/v3/detect'
        self.object_detect_url = 'https://api.megvii.com/imagepp/beta/detectsceneandobject'
        self.face_compare_url = 'https://api.megvii.com/facepp/v3/compare'
        self.api_key = '74N7z0o6dvJddH6khzBbfT7_J7n_vPaL'
        self.api_secret = 'krBWxLUE96yUDUk9GZArcek9fV96njf1'

        self.object_threshold = 20

        self.face_header = {
        'Accept-Encoding':'gzip, deflate',
        'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0",
        'Host': "http://megvii.com",
        'Referer': "http://megvii.com/",
        'X-Requested-With': "XMLHttpRequest"
        }

    def face_detect(self):
        s = requests.session()
        post_params = {'api_key': self.api_key,
                       'api_secret': self.api_secret,
                       'image_url': self.picurl,
                       'image_file': self.local_pic_path,
                       'return_attributes': 'gender,age,smiling,glass'}
        logger.info('face++ face detect picurl=%s, image_file=%s, post_params=%s', \
			self.picurl, self.local_pic_path, post_params)
        r = s.post(self.face_detect_url, data=post_params, timeout=1)
        face_result = r.content
        #TODO 可能报CONCURRENCY_LIMIT_EXCEEDED错误
        logger.info('face++ face detect = %s', face_result)
        return face_result

    def get_faces(self):
        try:
            face_result = self.face_detect()
            face_rst_json = json.loads(face_result)
            #TODO get first result by default
            sex = face_rst_json.get('faces')[0].get('attributes').get('gender').get('value')
            age = face_rst_json.get('faces')[0].get('attributes').get('age').get('value')
            glass = face_rst_json.get('faces')[0].get('attributes').get('glass').get('value')
            is_smile = face_rst_json.get('faces')[0].get('attributes').get('smile').get('value') \
                        >= face_rst_json.get('faces')[0].get('attributes').get('smile').get('threshold')

            reply_content = u'看起来是个%s, %s岁, %s戴眼镜, %s笑' % \
                                        (u'男生' if sex == 'Male' else u'女生', \
                                         age, \
                                         u'没有' if glass == 'None' else u'', \
                                         u'正在' if is_smile else u'没有')
            logger.info('face++ result = %s', reply_content)
            return reply_content
        except:
            logger.error(traceback.format_exc())
            return ''

    def face_compare(self, ft1, ft2):
        logger.warn('face_compare %s with %s', ft1, ft2)
        s = requests.session()

        post_params = {'api_key': self.api_key,
                       'api_secret': self.api_secret,
                       'face_token1': ft1,
                       'face_token2': ft2}
        r = s.post(self.face_compare_url, data=post_params)
        face_result = r.content
        logger.warn('face++ compare = %s', face_result)
        return face_result

    def get_face_token(self, face_result):
        face_rst_json = json.loads(face_result)
        #TODO get first result by default
        face_token = face_rst_json.get('faces')[0].get('face_token')
        logger.warn('face_token=%s', face_token)
        return face_token

    def object_detect(self):
        logger.info('face++ object detect picurl=%s', self.picurl)
        s = requests.session()
        post_params = {'api_key': self.api_key,
                       'api_secret': self.api_secret,
                       'image_url': self.picurl}
        r = s.post(self.object_detect_url, data=post_params)
        object_result = r.content
        logger.info('face++ object detect = %s', object_result)
        return object_result

    def get_objects(self):
        object_result = self.object_detect()
        try:
            object_result_json = json.loads(object_result)
            objects = []
            for obj in object_result_json.get('objects'):
                if float(obj.get('confidence')) > self.object_threshold:
                    obj_val = obj.get('value')
                    if obj_val == 'Person':
                        continue
                    objects.append('%s(%s)' % (obj_val, \
                                               TRANS_OBJ.get_trans(obj_val)))
            logger.info('face++ object result=%s', ','.join(objects))
            obj_rst_str = u'我看到图片里有%s哦！' % ','.join(objects) \
                if len(objects) > 0 else ''
            return obj_rst_str
        except:
            logger.error(traceback.format_exc())
            return ''

    def parse_result(self):
        return self.get_faces() + '\n' + self.get_objects()


class ImgProcessor(MessageProcessor):
    """
    image message processor
    """
    def __init__(self, msg):
        MessageProcessor.__init__(self)
        self.msg_dic = copy.deepcopy(msg.msg_dic)
        self.picurl = msg.get_pic_url()
        self.msg_id = msg.get_msg_id()
        self.face_plus_plus = FacePlusPlus(self.picurl)

    def gen_thumb_pic(self, pic_path, pic_name):
        #TODO add thumbnail pic process
        local_thumb_path = '%s/%s.jpg' % (WEIXIN_THUMBPIC_PATH, pic_name)
        return local_thumb_path 

    def save_pic(self, pic_url, pic_name):
        r = requests.get(pic_url)
        if r.status_code == 200:
            local_pic_path = '%s/%s.jpg' % (WEIXIN_PIC_PATH, pic_name)
            open(local_pic_path, 'wb').write(r.content)
            local_thumb_path = self.gen_thumb_pic(local_pic_path, pic_name)
            return (local_pic_path, local_thumb_path)
        return (None, None)

    def img_process(self):
        img_rst_str = PIC_NO_REC_MSG
        try:
            local_pic_path, local_thumb_path = self.save_pic(self.picurl, self.msg_id)
            self.face_plus_plus.local_pic_path = local_pic_path
            self.face_plus_plus.local_thumb_path = local_thumb_path
            img_rst_str = self.face_plus_plus.parse_result()
            logger.info('img_process = %s', img_rst_str)
            img_rst_str = img_rst_str.strip()
        except:
            logger.error('img_process error %s', traceback.format_exc())
            img_rst_str = PIC_NO_REC_MSG
        finally:
            self.msg_dic.update({'ResponseMsg': img_rst_str, \
                                'LocalPicUrl': self.face_plus_plus.local_pic_path, \
				'LocalThumbUrl': self.face_plus_plus.local_thumb_path})
            logger.info('Write img message to DB %s', self.msg_dic)
            self.insert_msg(self.msg_dic)
            return img_rst_str


if __name__ == '__main__':
    lym_img_url = 'http://mmbiz.qpic.cn/mmbiz_jpg/8TLtg6ibUImW4Fx9XuAkzCGgKKF4S3aptlpicU3KrzQbBrLLkw3AsMarA0u1YBlGMZrjvViba1iayFofXrXaoP0qaw/0'
    obj_img_url = 'https://mmbiz.qlogo.cn/mmbiz_jpg/WQanlFB5xs1hP8akr9Qz5g6gibzmaofjUStiaJQiaO4NHund4icSoqibVpdrD5fkMd0tq1jU4G7GnRpmzUpTCVhm2DQ/0?wx_fmt=jpeg'
    imgp = ImgProcessor(obj_img_url)
    imgp.img_process()
    #ft1 = get_face_token(face_detect('https://mmbiz.qlogo.cn/mmbiz_jpg/WQanlFB5xs1hP8akr9Qz5g6gibzmaofjUxcOlicV5R7IiaKCoOnwG41t0wr2fvHhnF97hgURfQnMQSsMuLfWcia05A/0?wx_fmt=jpeg'))
    #ft2 = get_face_token(face_detect('https://mmbiz.qlogo.cn/mmbiz_jpg/WQanlFB5xs1hP8akr9Qz5g6gibzmaofjUStiaJQiaO4NHund4icSoqibVpdrD5fkMd0tq1jU4G7GnRpmzUpTCVhm2DQ/0?wx_fmt=jpeg'))
    #face_compare(ft1, ft2)



