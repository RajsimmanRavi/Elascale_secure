#!/bin/bash
#This script basically deploys the IoT_app
#It deploys the following: sensor, rest_api and MySQL on appropriate worker nodes
#It is deployed as a stack using the iot_app_docker_compose.yml in docker_compose/

#First, we create the swarm worker nodes 
#hostname: "iot-core" label_key: "loc" label_value: "core"  
#hostname: "iot-edge" label_key: "loc" label_value: "edge"  
#hostname: "iot-agg-sensor" label_key: "loc" label_value: "agg-sensor"  
#label_key basically tells how to label the swarm node. It can be either be 'loc' or 'role'
#We provide these values to provision_vm.sh $1 -> vm_name $2 -> USERNAME $3 -> PASSWORD $4 -> label_key and $5 -> label_value

# Deploy nodes with these hostnames (if not created)
SCRIPTS_DIR="/home/ubuntu/Elascale_secure"
COMPOSE_DIR="$SCRIPTS_DIR/docker_compose"

CHECK_SENSOR=`$SCRIPTS_DIR/./get_node_role.sh agg-sensor`
CHECK_EDGE=`$SCRIPTS_DIR/./get_node_role.sh edge`
CHECK_CORE=`$SCRIPTS_DIR/./get_node_role.sh core`

if [  -z "$CHECK_SENSOR" ] || [ -z "$CHECK_EDGE" ] || [ -z "$CHECK_CORE" ]; then
    echo "One or more Application nodes not deployed yet. Beginnning deployment..."

    # Read Password for provisioning the VM
    echo -n Enter SAVI username: 
    read username
    
    # Read Password for provisioning the VM
    echo -n Password for user $username: 
    read -s password

else

   echo "All Nodes required are deployed"

fi
  
if [ -z "$CHECK_SENSOR" ]; then
    sudo $SCRIPTS_DIR/./provision_vm.sh "iot-agg-sensor" $username $password "loc" "agg-sensor"
fi

if [ -z "$CHECK_EDGE" ]; then
    sudo $SCRIPTS_DIR/./provision_vm.sh "iot-edge" $username $password "loc" "edge"
fi

if [ -z "$CHECK_CORE" ]; then
    sudo $SCRIPTS_DIR/./provision_vm.sh "iot-core" $username $password "loc" "core"
fi

#You need to edit the compose.yml to update the IP addresses for the following:
#REST_API_IP (EDGE_IP)
#MYSQL_IP (CORE_IP)

EDGE_NODE=`$SCRIPTS_DIR/./get_node_role.sh edge`
EDGE_IP="$(cut -d':' -f2 <<<"$EDGE_NODE")"
echo "EDGE IP: $EDGE_IP"

CORE_NODE=`$SCRIPTS_DIR/./get_node_role.sh core`
CORE_IP="$(cut -d':' -f2 <<<"$CORE_NODE")"
echo "CORE IP: $CORE_IP"

echo "Created all the worker nodes needed for IoT App deployment. Preparing for configuration..."

$SCRIPTS_DIR/./sleep_bar.sh 10 

echo "Updating values inside docker_compose files for IoT App deployment..."

#After provisioning the VMs, we have to edit the apropriate docker_compose files to change values 

#Change the IP address for REST_API_IP in iot_compose.yml file
sed -i "s/REST_API_IP: .*/REST_API_IP: $EDGE_IP/g" $COMPOSE_DIR/iot_app_compose.yml

#Change the IP address for MYSQL_IP in iot_compose.yml file
sed -i "s/MYSQL_IP: .*/MYSQL_IP: $CORE_IP/g" $COMPOSE_DIR/iot_app_compose.yml

#Finally deploy the iot_app as stack
sudo docker stack deploy -c $COMPOSE_DIR/iot_app_compose.yml iot_app

echo "IoT Application has been successfully deployed!"
