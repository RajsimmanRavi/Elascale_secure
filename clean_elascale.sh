#!/bin/bash

SCRIPTS_DIR="/home/ubuntu/Elascale_secure"

#remove the stacks and services first
sudo docker stack rm EK_monitor
sudo docker stack rm beats

PID=`ps -aux | grep autoscaler | grep tmux |  awk '{print $2}'`
sudo kill -9 $PID 
echo "Stopped Autoscaler if running..."

#Now, remove the worker node
sudo docker-machine rm -y iot-monitor
$SCRIPTS_DIR/./sleep_bar.sh 20
sudo docker node rm iot-monitor
