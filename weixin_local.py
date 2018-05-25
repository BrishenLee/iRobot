#-*- coding: utf-8 -*-

import os
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.options import define, options
from core.url import urlpatterns
from core.dbSchedule import DbSchedule
from core.taskSchedule import TaskSchedule

define('port', default=8000, help='run on the given port', type=int)


class Application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "core/templates"),
            static_path=os.path.join(os.path.dirname(__file__), "core/static"),
            debug=True,
            login_url='/login',
            #cookie_secret='MuG7xxacQdGPR7Svny1OfY6AymHPb0H/t02+I8rIHHE=',
        )
        super(Application, self).__init__(urlpatterns, **settings)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    # 执行定时任务
    #db_schedule = DbSchedule()
    #db_schedule.execute()
    task_schedule = TaskSchedule()
    task_schedule.redisSchedule(3600000)
    task_schedule.mongoSchedule(30000)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()
