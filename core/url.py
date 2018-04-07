#-*- coding: utf-8 -*-

import tornado.web
from core.mainInterface import MainHandler
from core.weixinInterface import WeixinHandler
from core.itchatInterface import ItChatHandler
from core.wxpyInterface import WxpyHandler
from core.imgInterface import ImgHandler

'''web解析规则'''

urlpatterns = [
    (r'/', MainHandler),
    (r'/weixin', WeixinHandler),
    (r'/itchat', ItChatHandler),
    (r'/wxpy', WxpyHandler),
    (r'/img', ImgHandler), 
   ]
