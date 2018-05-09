#!/bin/bash

SCRIPTS_DIR="/home/ubuntu/Elascale"

docker stack rm iot_app

echo -e "Removed IoT app stack!\n"

#Remove all the swarm nodes except monitor (swarm-master does not show up in this command output) 
NODES=( $(sudo docker-machine ls | awk '{print $1}' | grep -v 'NAME' | grep -v 'monitor') )

#Loop through each node and remove them 
for node in "${NODES[@]}"
do
    sudo docker-machine rm -y $node 
    $SCRIPTS_DIR/./sleep_bar.sh 20
    sudo docker node rm $node 
done
