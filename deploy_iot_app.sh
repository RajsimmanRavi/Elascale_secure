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

HOSTNAMES=("iot-core" "iot-edge" "iot-agg-sensor")
SCRIPTS_DIR="/home/ubuntu/Elascale_secure"
COMPOSE_DIR="$SCRIPTS_DIR/docker_compose"

# Read Password for provisioning the VM
echo -n Enter SAVI username: 
read username

# Read Password for provisioning the VM
echo -n Password for user $username: 
read -s password

label_key="loc"

for host in "${HOSTNAMES[@]}"
do
    label_value=`echo "${host#*-}"`
 
    check_node=`sudo docker node ls | grep "$host"`

    # Check if node exists before provisioning 
    if [[ -z $check_node ]];then
        echo "Node does not exist. Start provisioning..."
        sudo $SCRIPTS_DIR/./provision_vm.sh $host $username $password $label_key $label_value
    else
       echo "Node exists!"
    fi 
done

echo "Created all the worker nodes needed for IoT App deployment. Preparing for configuration..."

$SCRIPTS_DIR/./sleep_bar.sh 10 

echo "Updating values inside docker_compose files for IoT App deployment..."

#After provisioning the VMs, we have to edit the apropriate docker_compose files to change values 
#You need to edit the compose.yml to update the IP addresses for the following:
#REST_API_IP
#MYSQL_IP

#First get all the swarm nodes
NODES=( $(sudo docker-machine ls | awk '{print $1}' | grep -v 'NAME') )

#Loop through each node to find host IP address where Kafka has to be deployed and IP address of MySQL to be deployed
for node in "${NODES[@]}"
do
    #Inspect the node and get it's label
    #After grep, the output is '- loc=xxx'. In order to remove '- ', I use awk
    label=`sudo docker node inspect $node --pretty | grep "loc=" | awk '{print $2}'` 
    
    #Check if 'loc' is in that variable
    if [[ $label == "loc"* ]]
    then
        
        #Get only the substring that comes after '='. Hence, we get the 'xxx' value from loc=xxx
        label_val=${label#*=}

        #REST_API_IP is the host with the label_val='edge'
        if [[ $label_val == "edge" ]]
        then
        
            #Get the IP of that node
            #Grep Address from the inspect command
            #Remove any in-between spaces (using tr)
            #Get the second argument with delimiter '=' (using awk)
            REST_API_IP=`sudo docker node inspect $node --pretty | grep Address | tr -d " \t\n\r" | awk -F ':' {'print $2'}`

        #MYSQL_IP is the host with the label_val='core'
        elif [[ $label_val == "core" ]]
        then 
 
            #Do the same as above command
            MYSQL_IP=`sudo docker node inspect $node --pretty | grep Address | tr -d " \t\n\r" | awk -F ':' {'print $2'}`

        fi    
    fi
done

#Change the IP address for REST_API_IP in iot_compose.yml file
sed -i "s/REST_API_IP: .*/REST_API_IP: $REST_API_IP/g" $COMPOSE_DIR/iot_app_compose.yml

#Change the IP address for MYSQL_IP in iot_compose.yml file
sed -i "s/MYSQL_IP: .*/MYSQL_IP: $MYSQL_IP/g" $COMPOSE_DIR/iot_app_compose.yml

#Finally deploy the iot_app as stack
sudo docker stack deploy -c $COMPOSE_DIR/iot_app_compose.yml iot_app

echo "IoT Application has been successfully deployed!"
