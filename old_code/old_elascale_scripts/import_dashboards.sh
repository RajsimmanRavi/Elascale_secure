#!/bin/bash

SCRIPTS_DIR="/home/ubuntu/Elascale"
CONFIG_DIR="$SCRIPTS_DIR/config"
ELASTIC_IP=`$SCRIPTS_DIR/./get_elastic_ip.sh`
ELASTIC_PORT="9200"

#Want to check how long it has been waiting for the port to be open
#If it's been more than 60 seconds, then exit this file and re-deploy EK
#This problem happens if it's a brand new VM with a new IP address (kind of odd)
COUNTER=0
#Check if port $ELASTIC_IP:9200 is up and running
for (( ; ; ))
do
    #If port is not open for more than 60 seconds, re-deploy EK
    if [[ $COUNTER -gt 60 ]]
    then
        echo "failed"
        exit 0
    fi 

    #Checks if port open. If 0 -> open, 1 -> closed
    port_open=`nc -w 5 $ELASTIC_IP $ELASTIC_PORT </dev/null; echo $?`    
    
    if [[ $port_open == "1" ]]
    then
        echo "Port is closed. Retrying after 5 seconds"
        sleep 5
        let COUNTER=COUNTER+5
    else 
        echo "Port is open! Staring import..."
        break
    fi
done
 
elasticdump --input=$CONFIG_DIR/dash_templates/index_analyzer.json --output=http://$ELASTIC_IP:$ELASTIC_PORT/.kibana --type=analyzer
echo "Done Importing Analyzer"
elasticdump --input=$CONFIG_DIR/dash_templates/index_mapping.json --output=http://$ELASTIC_IP:$ELASTIC_PORT/.kibana --type=mapping
echo "Done Importing Mapping"
elasticdump --input=$CONFIG_DIR/dash_templates/index_data.json --output=http://$ELASTIC_IP:$ELASTIC_PORT/.kibana --type=data
echo "Done Importing Data"
