#!/bin/bash

SCRIPTS_DIR="/home/ubuntu/Elascale_secure"
CONFIG_DIR="$SCRIPTS_DIR/config"
ELASTIC_NODE=`$SCRIPTS_DIR/./get_node_role.sh monitor`
ELASTIC_IP="$(cut -d':' -f2 <<<"$ELASTIC_NODE")"
ELASTIC_PORT="9200"

#Want to check how long it has been waiting for the port to be open
#If it's been more than 60 seconds, then exit this file and re-deploy EK
#This problem happens if it's a brand new VM with a new IP address (kind of odd)
COUNTER=0
#Check if port $ELASTIC_IP:9200 is up and running
for (( ; ; ))
do
    #If port is not open for more than 60 seconds, re-deploy EK
    if [[ $COUNTER -gt 120 ]]
    then
        echo "failed"
        exit 0
    fi 

    check_link=$(curl https://$ELASTIC_IP:$ELASTIC_PORT --insecure)
    
    # If you get a response with test "You know, for Search". Then, it's up and running  
    if [[ "$check_link" == *"You Know, for Search"* ]]
    then
        echo "Elasticsearch is up and running. Starting import ..." 
        break
    else 
        echo "Elasticsearch is not up yet. Retrying after 5 seconds..."
        sleep 5
        let COUNTER=COUNTER+5
    fi
done

NODE_TLS_REJECT_UNAUTHORIZED=0 elasticdump --input=$CONFIG_DIR/dash_templates/index_analyzer.json --output=https://$ELASTIC_IP:$ELASTIC_PORT/.kibana --type=analyzer
echo "Done Importing Analyzer"
NODE_TLS_REJECT_UNAUTHORIZED=0 elasticdump --input=$CONFIG_DIR/dash_templates/index_mapping.json --output=https://$ELASTIC_IP:$ELASTIC_PORT/.kibana --type=mapping
echo "Done Importing Mapping"
NODE_TLS_REJECT_UNAUTHORIZED=0 elasticdump --input=$CONFIG_DIR/dash_templates/index_data.json --output=https://$ELASTIC_IP:$ELASTIC_PORT/.kibana --type=data
echo "Done Importing Data"
