#!/bin/bash

# Raj: Deploys Metricbeat and Dockbeat on Docker swarm nodes 

# Check if arguments given
if [[ $# -eq 0 ]] ; then
    echo "Error: you need to provide the IP address of Elasticsearch's Host"
    exit 1
fi

ELASTIC_IP="$1"
SCRIPTS_DIR="/home/ubuntu/Elascale_secure"
COMPOSE_DIR="$SCRIPTS_DIR/docker_compose"
CONFIG_DIR="$SCRIPTS_DIR/config"
CONFIG_DIR="$SCRIPTS_DIR/certs"
THIS_NODE_HOSTNAME=`hostname`
ADD_HOST_CMD="echo '$ELASTIC_IP elasticsearch' | sudo tee -a /etc/hosts > /dev/null"

#This is for deploying the dockbeat
VOLUME_DIR="/volumes/dockbeat-logs"

# Ok, the command is huge. Let me break it down.
# "docker node ls" gives us the nodes and it's hostnames.
# awk {print $2" "$3} gives us only the hostnames.
# sed 's/*//g' removes the asterisk
# sed 's/Ready//g' removes the string "Ready" because we had that when we printed $3
# sed 's/HOSTNAME//g' removes the string "HOSTNAME" from the title of the output
# sed 's/STATUS//g' removes the string "STATUS" from the title of the output
# sed '/^$/d'` removes empty lines from the output

# Hence this provides only the hostnames of the nodes we want to deploy dockbeat and metricbeat.
# Store this in an array
NODES=( $(sudo docker node ls | awk '{print $2}' | sed 's/*//g' | sed 's/Ready//g' |sed 's/HOSTNAME//g' | sed 's/STATUS//g'| sed '/^$/d') )

# -- This is old configuration. Now we just need to add elasticsearch to /etc/hosts on each node -- #

# Let's start with the dockbeat. First replace ELASTIC_IP with the 1st argument
#sed -i "s/hosts: \[\".*:9200\"\]/hosts: \[\"$ELASTIC_IP:9200\"\]/g" $CONFIG_DIR/dockbeat.yml
# Then, let's do the same for metricbeat. 
#sed -i "s/hosts: \[\".*:9200\"\]/hosts: \[\"$ELASTIC_IP:9200\"\]/g" $CONFIG_DIR/metricbeat.yml

# -- End of old configuration -- #

for hostname in "${NODES[@]}"
do
    # Let's replace name in metricbeat.yml
    # Replace `name: "*"` with `name: "hostname"`
    sed -i "s/name: \".*\"/name: \"$hostname\"/g" $CONFIG_DIR/metricbeat.yml

    # send the files to the node
    sudo docker-machine scp $CONFIG_DIR/dockbeat.yml $hostname:~
    sudo docker-machine scp $CONFIG_DIR/metricbeat.yml $hostname:~

    # we also need to make sure /volumes/dockbeat-logs/ is in each node
    sudo docker-machine ssh $hostname 'sudo mkdir -p /volumes/dockbeat-logs' 
    
    # Create /home/ubuntu/certs folder to store elasticsearch_certificate.pem
    sudo docker-machine ssh $hostname 'sudo mkdir /home/ubuntu/certs' 

    # send elasticsearch_certificate.pem to the node
    sudo docker-machine scp $CERTS_DIR/elasticsearch_certificate.pem $hostname:~/certs

    # we need to add elasticsearch ip mapping to /etc/hosts for each node
    #sudo docker-machine ssh $hostname $ADD_HOST_CMD

    echo "Done sending files for node: $hostname"
done

#We still need to do it for this node itself
sed -i "s/name: \".*\"/name: \"$THIS_NODE_HOSTNAME\"/g" $CONFIG_DIR/metricbeat.yml

#Copy it to the home folder 
cp $CONFIG_DIR/dockbeat.yml ~
cp $CONFIG_DIR/metricbeat.yml ~

#Create certs folder if it doesn't exist 
if [ ! -d "/home/ubuntu/certs" ] 
then 
    sudo mkdir /home/ubuntu/certs
fi

#Copy nginx certificate to the home/ubuntu/certs folder
cp $CERTS_DIR/elasticsearch_certificate.pem /home/ubuntu/certs/

echo "Done putting files to the home folder for this node: $THIS_NODE_HOSTNAME"

if [ ! -d "$VOLUME_DIR" ]
then
    #********** Create Elascale directory and fetch the scripts ****************
    sudo mkdir -p $VOLUME_DIR
    echo "Creating $VOLUME_DIR for dockbeat in the host"
fi       

#Edit the beats-compose.yml file to replace the Elasticsearch IP 
sed -i "s/elasticsearch:.*/elasticsearch:$ELASTIC_IP\"/g" $COMPOSE_DIR/beats-compose.yml

echo "Changed ELASTIC_IP in beats-compose.yml"

echo "Deploying Metricbeat and Dockbeat on swarm nodes..."

sleep 2 

sudo docker stack deploy -c $COMPOSE_DIR/beats-compose.yml beats
