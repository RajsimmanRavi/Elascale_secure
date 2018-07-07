#!/bin/bash

# RR: I created this script for CNSM Evaluation for creating spatial/temporal and concept drift scenarios

# For Temporal
for i in `seq 1 9`;
do
    if [[ "$i" -ne 7  ]]; then
    #if [[ "$i" -ne 4  ]] || [[ "$i" -ne 7 ]]; then
    
        sudo docker service scale iot_app_sensor=10
        
        sleep 450s

        sudo docker service scale iot_app_sensor=1

        sleep 450s
    
    else
        sudo docker service scale iot_app_sensor=10
        
        sleep 450s
        
        sudo docker service scale iot_app_sensor=1
        
        sleep 150s

        sudo docker service scale iot_app_sensor=20

        sleep 150s

        sudo docker service scale iot_app_sensor=1

        sleep 150s

    fi
    
done    

sudo docker service scale iot_app_sensor=1

# For Spatial anomaly 
#sleep 3600s # sleep for 1 hour
#
#for i in `seq 1 5`;
#do
#    sudo docker service scale iot_app_sensor=10
#
#    sleep 120s
#
#    sudo docker service scale iot_app_sensor=1
#
#    sleep 60s
#
#done    

# For concept drift testing
#sleep 3600s
#sudo docker service scale iot_app_sensor=10
#sleep 4000s
#sudo docker service scale iot_app_sensor=1

#while [ 1 ]
#do 
#    sudo docker service scale iot_app_sensor=8
#
#    sleep 1800s
#
#    sudo docker service scale iot_app_sensor=1
#
#    sleep 1800s
#
#done
