#!/bin/bash

# Check if arguments given
if [[ $# -ne 2 ]] ; then
    echo "Error: you need to provide the IP address of Elasticsearch Host and the hostname of the monitor VM"
    exit 1
fi

SCRIPTS_DIR="/home/ubuntu/Elascale_secure"
COMPOSE_DIR="$SCRIPTS_DIR/docker_compose"
CONFIG_DIR="$SCRIPTS_DIR/config/"
CERTS_DIR="$SCRIPTS_DIR/certs/"

ELASTIC_IP="$1"
MONITOR_VM="$2"

# Now, replace the IP in ek-compose.yml to the ELASTIC_IP
sed -i "s/\"elasticsearch:.*\"/\"elasticsearch:$ELASTIC_IP\"/g" $COMPOSE_DIR/ek-compose.yml

echo "sending certs directory to the monitor VM"
sudo docker-machine scp -r $CONFIG_DIR $MONITOR_VM:~

echo "sending config directory to the monitor VM"
sudo docker-machine scp -r $CERTS_DIR $MONITOR_VM:~

echo "Changing setting for monitor VM to increase virtual memory (need for Elasticsearch)"
sudo docker-machine ssh $MONITOR_VM "sudo sysctl -w vm.max_map_count=262144"

echo "Deploying EK services"

sudo docker stack deploy -c $COMPOSE_DIR/ek-compose.yml EK_monitor

echo "Waiting for Elasticsearch to be up and running"

$SCRIPTS_DIR/sleep_bar.sh 60

#check if succeeded or failed. If it failed to import, re-deploy EK again

#check_link=$(curl https://$ELASTIC_IP:$ELASTIC_PORT --insecure)

# If you get a response with test "You know, for Search". Then, it's up and running  
#if [[ "$check_link" == *"You Know, for Search"* ]]
#then
#    echo "Elasticsearch is up and running. Starting import ..." 
#    break
#else 
#    echo "Elasticsearch is not up yet. Retrying after 5 seconds..."
#    sleep 5
#    let COUNTER=COUNTER+5
#fi
#    echo "Failed to deploy Elasticsearch and Kibana because Elasticsearch port (9200) not open"
#    echo "Hence, re-deploying EK"
#    sudo docker stack rm EK_monitor
#
#    $SCRIPTS_DIR/sleep_bar.sh 10
#
#    # Name of the stack must contain the keyword 'monitor' in order for nginx to work
#    sudo docker stack deploy -c $COMPOSE_DIR/ek-compose.yml EK_monitor

echo "Completed ELK deployment"
