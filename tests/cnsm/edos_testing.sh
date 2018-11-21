#!/bin/bash

# RR: I created this script for CNSM Evaluation for creating spatial/temporal and concept drift scenarios

# For Temporal
temporal(){
  for i in `seq 1 9`;
  do
      if [[ "$i" -ne 7  ]]; then
      #if [[ "$i" -ne 4  ]] || [[ "$i" -ne 7 ]]; then
      # I had 10 and 20 originally for CNSM
      
          sudo docker service scale iot_app_sensor=6
          
          sleep 450s
  
          sudo docker service scale iot_app_sensor=1
  
          sleep 450s
      
      else
          sudo docker service scale iot_app_sensor=6
          
          sleep 450s
          
          sudo docker service scale iot_app_sensor=1
          
          sleep 150s
  
          sudo docker service scale iot_app_sensor=20
  
          sleep 450s
          #sleep 900s
  
          sudo docker service scale iot_app_sensor=1
  
          sleep 150s
  
      fi
      
  done    
  
}

# For Spatial anomaly 
spatial(){
  sudo docker service scale iot_app_sensor=1
  sleep 3600s # sleep for 1 hour
  
  for i in `seq 1 5`;
  do
      sudo docker service scale iot_app_sensor=12
  
      sleep 120s
  
      sudo docker service scale iot_app_sensor=1
  
      sleep 60s
  
  done  
  # just making sure
  sudo docker service scale iot_app_sensor=1
  sleep 2700s
}

# For concept drift testing
concept_drift(){
  # I had 10 for old IoT App
  sleep 3600s
  sudo docker service scale iot_app_sensor=20
  sleep 3600s
  sudo docker service scale iot_app_sensor=1
}

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 ANOMALY TYPE(temporal/spatial/concept_drift)" >&2
  exit 1
fi

if [ $1 = "temporal" ]; then
  temporal
elif [ $1 == "spatial" ]; then
  spatial
else
  concept_drift
fi
