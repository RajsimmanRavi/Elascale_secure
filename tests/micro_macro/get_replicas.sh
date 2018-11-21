#!/bin/bash

FILE_NAME="replicas.csv"
DURATION=1800
SLEEP_TIME=30

rm $FILE_NAME

# HEADER
echo "TIME,SENSOR REPLICAS,REST API REPLICAS,IOT-EDGE REPLICAS" >> $FILE_NAME

START=`date +%s`
while [ $(( $(date +%s) - $DURATION )) -lt $START ]; do  

    NOW=$(date +"%Y-%m-%d %H:%M:%S")
    SENSOR_REPLICAS=`sudo docker service inspect iot_app_sensor -f '{{ .Spec.Mode.Replicated.Replicas }}'|tr -d ' '`
    REST_API_REPLICAS=`sudo docker service inspect iot_app_rest_api -f '{{ .Spec.Mode.Replicated.Replicas }}'|tr -d ' '`
    IOT_EDGE_REPLICAS=`sudo docker node ls | grep "iot-edge*" | awk '{print $2}' | wc -l`
    
    echo "$NOW,$SENSOR_REPLICAS,$REST_API_REPLICAS,$IOT_EDGE_REPLICAS" >> $FILE_NAME

    sleep $SLEEP_TIME 

done
