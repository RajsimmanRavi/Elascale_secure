#!/bin/bash

# RR: I created this script for Testing Autoscaler and comparison between use of different policies

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 Type: 'simple' or 'spatial'" >&2
  exit 1
fi

simple(){
  NOW=$(date +"%Y-%m-%d %H:%M:%S")
  echo "Starting testing now: $NOW"
  
  sudo docker service scale iot_app_sensor=1 
  sleep 300s
  
  NOW=$(date +"%Y-%m-%d %H:%M:%S")
  echo "Starting to scale high now: $NOW"
  
  sudo docker service scale iot_app_sensor=12
  sleep 600s
  
  NOW=$(date +"%Y-%m-%d %H:%M:%S")
  echo "Starting to scale back now: $NOW"
  
  sudo docker service scale iot_app_sensor=1 
  sleep 300s
  
  NOW=$(date +"%Y-%m-%d %H:%M:%S")
  echo "Ending testing now: $NOW"
}

# For Spatial anomaly 
spatial(){
  
  echo "Starting Yo Yo scaling test..."
  for i in `seq 1 5`;
  do
      
      NOW=$(date +"%Y-%m-%d %H:%M:%S")
      echo "Starting to scale high now: $NOW"
      
      sudo docker service scale iot_app_sensor=12
  
      sleep 30s
  
      NOW=$(date +"%Y-%m-%d %H:%M:%S")
      echo "Starting to scale back now: $NOW"
      
      sudo docker service scale iot_app_sensor=1
  
      sleep 30s
  
  done    
  echo "Finished testing Yo Yo..."
}

if [ $1 = "simple" ];then
    simple
else
    spatial
fi
