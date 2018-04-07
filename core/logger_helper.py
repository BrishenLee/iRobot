#-*- coding: utf-8 -*-

import logging
from logging import Logger
from utils import *
from logging.handlers import TimedRotatingFileHandler

'''日志管理类'''


#TODO log_path
def init_logger(logger_name, log_path=PROJ_LOG_FILE):
    if logger_name not in Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)  # 设置最低级别
        df = '%Y-%m-%d %H:%M:%S'
        format_str = '[%(asctime)s]: %(name)s %(levelname)s %(lineno)s %(message)s'
        formatter = logging.Formatter(format_str, df)
        # handler all
        try:
            handler1 = TimedRotatingFileHandler(log_path, when='D', interval=1, backupCount=7)
        except Exception:
            raise IOError('log path error !')
        handler1.setFormatter(formatter)
        handler1.setLevel(logging.DEBUG)
        logger.addHandler(handler1)
        # handler error
        try:
            handler2 = TimedRotatingFileHandler(log_path + '.wf', when='D', interval=1, backupCount=7)
        except Exception:
            raise IOError('log path error !')
        handler2.setFormatter(formatter)
        handler2.setLevel(logging.ERROR)
        logger.addHandler(handler2)

        # console
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        # 设置日志打印格式
        console.setFormatter(formatter)
        # 将定义好的console日志handler添加到root logger
        logger.addHandler(console)
    
    logger = logging.getLogger(logger_name)
    return logger


logger = init_logger('runtime-log')

if __name__ == '__main__':
    logger.debug('test-debug')
    logger.info('test-info')
    logger.warn('test-warn')
    logger.error('test-error')
