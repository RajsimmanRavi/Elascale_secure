#!/bin/bash

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 FILE_NAME DURATION (secs)" >&2
  exit 1
fi

rm $1

echo "Time,Sensor_replicas,REST_API_replicas" >> $1

START=`date +%s`
while [ $(( $(date +%s) - $2 )) -lt $START ]; do  

  sensor_replicas=`sudo docker service ls --filter name=iot_app_sensor --format '{{ .Replicas }}' | awk -F '/' '{print $1}'`
  rest_replicas=`sudo docker service ls --filter name=iot_app_rest_api --format '{{ .Replicas }}' | awk -F '/' '{print $1}'`
  NOW=$(date +"%Y-%m-%d %R")
  echo "$NOW,$sensor_replicas,$rest_replicas" >> $1

  sleep 30 

done

