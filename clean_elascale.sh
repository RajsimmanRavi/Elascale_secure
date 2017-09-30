#!/bin/bash

SCRIPTS_DIR="/home/ubuntu/Elascale_secure"

#remove the stacks and services first
sudo docker stack rm EK_monitor
sudo docker stack rm beats
sudo docker stack rm elascale  
sudo docker service rm ui

#Now, remove the worker node
sudo docker-machine rm -y monitor
$SCRIPTS_DIR/./sleep_bar.sh 20
sudo docker node rm monitor
