#!/bin/bash

#This script basically creates a VM (based on below specs) and joins that node to swarm as worker.
#It also labels the node as specified 

#This should take a few arguments 
#1. VM name
#2. SAVI Username 
#3. SAVI Password 
#4. Label_key (can be 'role' or 'loc')
#5. Label_value (can be 'monitor' or one of the following: 'core', 'edge', 'agg-sensor'

VM_NAME="$1"
USERNAME="$2"
PASSWORD="$3"
LABEL_KEY="$4"
LABEL_VALUE="$5"

DEFAULT_REGION="EDGE-TR-1"
DEFAULT_TENANT="demo1"
DEFAULT_AUTH_URL="http://iam.savitestbed.ca:5000/v2.0"

JOIN_COMMAND="sudo "`sudo docker swarm join-token worker | grep -v 'add' | tr -d '\' 2> /dev/null`
SCRIPTS_DIR="/home/ubuntu/Elascale_secure"

check_vm=`sudo docker-machine ls | grep $VM_NAME`

VM_FLAVOR="m1.medium"

#Hamzeh requested to create large flavor for iot-core VM for future deployments
#Hence, I will create the snippet, but comment them (so they can be used for future deployments)
#if [[ $VM_NAME == "iot-core" ]]
#then 
#    VM_FLAVOR="m1.large"
#fi

if [[ -z $check_vm ]]
then

    read -p "Tenant ($DEFAULT_TENANT): " tenant
    tenant=${tenant:-$DEFAULT_TENANT}
    echo $tenant
    
    read -p "Region ($DEFAULT_REGION): " region
    region=${region:-$DEFAULT_REGION}
    echo $region
    
    read -p "Auth URL ($DEFAULT_AUTH_URL): " auth_url
    auth_url=${auth_url:-$DEFAULT_AUTH_URL}
    echo $auth_url

    network_name="`echo "$tenant" | tr '[:upper:]' '[:lower:]'`-net"

    sudo docker-machine create --driver openstack \
      --openstack-auth-url "$auth_url" \
      --openstack-insecure \
      --openstack-flavor-name $VM_FLAVOR --openstack-image-name "Ubuntu-14-04" \
      --openstack-tenant-name "$tenant" --openstack-region "$region" \
      --openstack-net-name "$network_name" \
      --openstack-sec-groups "savi-iot" --openstack-ssh-user "ubuntu" \
      --openstack-username $USERNAME --openstack-password $PASSWORD \
      $VM_NAME
else 
    "VM $VM_NAME deployed already"
fi 

echo "Preparing for further configuration..."

$SCRIPTS_DIR/./sleep_bar.sh 10

echo "Add node to swarm as worker"

sudo docker-machine ssh $VM_NAME $JOIN_COMMAND

$SCRIPTS_DIR/./sleep_bar.sh 5 

echo "Label the node"

sudo docker node update --label-add $LABEL_KEY=$LABEL_VALUE $VM_NAME
