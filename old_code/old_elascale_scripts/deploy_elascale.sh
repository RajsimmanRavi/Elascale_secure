#!/bin/bash

SCRIPTS_DIR="/home/ubuntu/Elascale"
CONFIG_DIR="$SCRIPTS_DIR/config"
COMPOSE_DIR="$SCRIPTS_DIR/docker_compose"
HOSTNAME=`hostname`
HOST_IP=`ifconfig eth0 | grep 'inet addr' | cut -d ':' -f 2 | awk '{print $1}'`


#Command-line arguments for provisioning VM
VM_NAME="iot-monitor"
LABEL_KEY="role" # We want to label the node role=elascale
LABEL_VALUE="elascale" # same as above

#check if the monitor VM is already deployed
check_monitor=`sudo docker-machine ls | grep monitor`

if [[ -z $check_monitor ]]
then

    # Read Username for provisioning the VM
    echo -n Enter SAVI username: 
    read USERNAME 

    # Read Password for provisioning the VM
    echo -n Password for user $USERNAME: 
    read -s PASSWORD 

    # Empty line for better printing 
    echo

    $SCRIPTS_DIR/./provision_vm.sh $VM_NAME $USERNAME $PASSWORD $LABEL_KEY $LABEL_VALUE
else 
   echo "monitor VM already deployed. Skipping step."

fi 

#Get the IP address of the provisioned VM (has the label 'elascale')
ELASTIC_IP=`$SCRIPTS_DIR/./get_elastic_ip.sh`

echo "ELASTIC_IP: $ELASTIC_IP"

$SCRIPTS_DIR/./deploy_ek.sh $ELASTIC_IP $VM_NAME

echo "Deployed Elasticsearch and Kibana. Preparing to import dashboards and templates"

$SCRIPTS_DIR/import_dashboards.sh

$SCRIPTS_DIR/./sleep_bar.sh 20

echo "Starting Beats deployment"

$SCRIPTS_DIR/./deploy_beats.sh $ELASTIC_IP

#Let's create the Elascale UI
echo "Deployed Beats. Starting Elascale service UI"

sleep 2

#Ok, this docker service command is huge. Let's break it down
# -p 8888:8888 - bind the host port to the container port 
# --detach=true - detach the service and run it in background
# --constraint node.hostname==$HOSTNAME - run it on this host only
# --mount=type=bind,src=$SCRIPTS_DIR/conf,dst=$SCRIPTS_DIR/conf - bind the host's folder to the container, such that changes made to this folder (by the container) will be used by the host as well
# --mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock - bind the docker sock to get docker client information from inside the container
# perplexedgamer/ui - container image
# The remaining flags are args to the image 

sudo docker service create -p 8888:8888 --detach=true --name ui --constraint node.hostname==$HOSTNAME --mount=type=bind,src=$CONFIG_DIR,dst=$CONFIG_DIR --mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock perplexedgamer/ui:v4 --host_ip=$HOST_IP --elastic_ip=$ELASTIC_IP --micro=$CONFIG_DIR/microservices.ini --macro=$CONFIG_DIR/macroservices.ini

#Now, let's start the Elascale Engine

#First, change the config.ini file to update the IP addresses of the hosts and Elastic IPs
python $SCRIPTS_DIR/change_config_ini.py $HOST_IP $ELASTIC_IP

#Now, deploy the Elascale stack
echo "Starting Elascale Engine deployment"

sudo docker stack deploy -c $COMPOSE_DIR/elascale-compose.yml elascale

echo "Deployed Everything. You can view the Elascale UI at: http://$HOST_IP:8888"
echo "For more detailed information, you can view the Kibana UI at: http://$ELASTIC_IP:5601"

echo "Please wait for a few minutes for all the services to be up and running. You can verify it by using the followning command: sudo docker service ls"

sudo docker service ls
