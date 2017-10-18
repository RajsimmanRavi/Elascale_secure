#!/bin/bash

SCRIPTS_DIR="/home/ubuntu/Elascale_secure"
CONFIG_DIR="$SCRIPTS_DIR/config"
COMPOSE_DIR="$SCRIPTS_DIR/docker_compose"
HOSTNAME=`hostname`
MASTER_IP=`$SCRIPTS_DIR/./get_node_role_ip.sh master`
KIBANA_USERNAME="elascale"
KIBANA_PASSWORD="savi_elascale"

#Command-line arguments for provisioning VM
VM_NAME="iot-monitor"
LABEL_KEY="role" # We want to label the node role=monitor
LABEL_VALUE="monitor" # same as above

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

#Get the IP address of the provisioned VM (has the label 'monitor')
ELASTIC_IP=`$SCRIPTS_DIR/./get_node_role_ip.sh monitor`

echo "ELASTIC_IP: $ELASTIC_IP"

# Now that we have the ELASTIC_IP and MASTER_IP, we can create the certificates

sudo $SCRIPTS_DIR/./create_certs.sh $ELASTIC_IP $MASTER_IP

echo "Created Certificates for Elasticsearch, Kibana and the Elascale UI"

# Create Basic authentication for Kibana UI
sudo htpasswd -b -c /home/ubuntu/Elascale_secure/config/.htpasswd $KIBANA_USERNAME $KIBANA_PASSWORD

$SCRIPTS_DIR/./deploy_ek.sh $ELASTIC_IP $VM_NAME

echo "Deployed Elasticsearch and Kibana. Preparing to import dashboards and templates"

$SCRIPTS_DIR/import_dashboards.sh

$SCRIPTS_DIR/./sleep_bar.sh 20

echo "Starting Beats deployment"

$SCRIPTS_DIR/./deploy_beats.sh $ELASTIC_IP

#Let's create the Elascale UI
echo "Deployed Beats. Starting Elascale service UI"

sleep 2

#Now, let's start the Elascale Engine and the UI

#First, change the config.ini file to update the IP addresses of the hosts and Elastic IPs
python $SCRIPTS_DIR/change_config_ini.py $MASTER_IP $ELASTIC_IP $HOSTNAME

# Change the elasticsearch IP address on the elascale-ui-compose.yml 
sed -i "s/elasticsearch:.*/elasticsearch:$ELASTIC_IP\"/g" $COMPOSE_DIR/elascale-ui-compose.yml

# Change HOST_IP to point to Master's IP Address
sed -i "s/HOST_IP :.*/HOST_IP : \"$MASTER_IP\"/g" $COMPOSE_DIR/elascale-ui-compose.yml

# Change ELASTIC_IP to point to ELASTIC_IP's IP Address
sed -i "s/ELASTIC_IP :.*/ELASTIC_IP : \"$ELASTIC_IP\"/g" $COMPOSE_DIR/elascale-ui-compose.yml

#Now, deploy the Elascale stack
echo "Starting Elascale Engine deployment"

sudo docker stack deploy -c $COMPOSE_DIR/elascale-ui-compose.yml elascale

echo "Deployed Everything. You can view the Elascale UI at: https://$MASTER_IP:8888"
echo "For more detailed information, you can view the Kibana UI at: https://$ELASTIC_IP:5601"

echo "Please wait for a few minutes for all the services to be up and running. You can verify it by using the followning command: sudo docker service ls"

sudo docker service ls
