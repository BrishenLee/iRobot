#!/bin/bash

#前提：redis服务已启动
#echo "Start natapp ..."
#./bin/natapp --authtoken=eb6ea0912a6d3528 &

pid=`ps -ef | grep -v grep | grep mongod | awk '{print $2}'`
if [ "$pid" == "" ];then
    echo "Start mongodb ..."
    nohup mongod --dbpath ~/mongodb/ 1>>log/weixin.log 2>>log/weixin.log &
fi

#nohup ./bin/ngrok -config=bin/ngrok.cfg -subdomain brishen 8000 1>> log/weixin.log 2>> log/weixin.log & 
echo "Start mofasuidao ..."
ps -ef | grep mofasuidao | grep -v grep | awk '{print $2}' | xargs kill -9
nohup ./bin/mofasuidao  14e8faf1-fd65-4eb9-914f-b1c6cd8b91d1 &

echo "Clean web service ..."
pid=`ps -ef | grep -v grep | grep weixin_local.py | awk '{print $2}'`
if [ "$pid" == "" ];then
    echo "No process found"
else
    echo "Kill current process "$pid
    kill -9 $pid
fi

echo "Start web service ..."
nohup python weixin_local.py 8000 1>> log/weixin.log 2>> log/weixin.log &
echo "Done."
