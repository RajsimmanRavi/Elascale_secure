#!/bin/bash

# RR: I created this script for Testing Autoscaler and comparison between use of different policies

TIME_INTERVAL=300s

function update_iot_edge_ips {

  
    IPS=`sudo docker-machine ls --filter 'name=iot-edge' --format {{.URL}} | grep -o -E '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | tr '\n' ',' | rev | cut -c 2- | rev`
    ENV_VAR="REST_API_IPS=$IPS"
    
    echo "Current IPs: $IPS"
    sudo docker service update --env-add $ENV_VAR iot_app_sensor
}

NOW=$(date +"%Y-%m-%d %H:%M:%S")
echo "Starting testing now: $NOW"
update_iot_edge_ips
sudo docker service scale iot_app_sensor=1 
sleep $TIME_INTERVAL

NOW=$(date +"%Y-%m-%d %H:%M:%S")
echo "Increasing Sensors: $NOW"
update_iot_edge_ips
#sudo docker service scale iot_app_sensor=15
sudo docker service scale iot_app_sensor=30
sleep $TIME_INTERVAL

#NOW=$(date +"%Y-%m-%d %H:%M:%S")
#echo "Increasing Sensors: $NOW"
#update_iot_edge_ips
#sudo docker service scale iot_app_sensor=30
#sleep $TIME_INTERVAL
#
#NOW=$(date +"%Y-%m-%d %H:%M:%S")
#echo "Increasing Sensors: $NOW"
#update_iot_edge_ips
##sudo docker service scale iot_app_sensor=15
#sudo docker service scale iot_app_sensor=30
#sleep $TIME_INTERVAL

NOW=$(date +"%Y-%m-%d %H:%M:%S")
echo "Starting to scale back now: $NOW"
update_iot_edge_ips
sudo docker service scale iot_app_sensor=1
sleep $TIME_INTERVAL

NOW=$(date +"%Y-%m-%d %H:%M:%S")
echo "Ending testing now: $NOW"
