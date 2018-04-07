# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import traceback
import tornado.web
import tornado.ioloop
from utils import *
from logger_helper import logger


class MainHandler(tornado.web.RequestHandler):
    def prepare(self):
        """
        overwrite setup
        """
        logger.info('===== MAIN MESSAGE START =====')

    def on_finish(self):
        """
        overwrite teardown
        """
        logger.info('===== MAIN MESSAGE END =====\n')

    def get(self):
        self.render('index.html')

if __name__ == "__main__":
    pass

