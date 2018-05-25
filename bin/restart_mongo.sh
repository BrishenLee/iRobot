#!/bin/bash

pid=`ps -ef | grep -v grep | grep mongod | awk '{print $2}'`
if [ "$pid" == "" ];then
    echo "Start mongodb ..."
    sudo mongod --config /etc/mongodb.conf
fi
sleep 5
exit 0
