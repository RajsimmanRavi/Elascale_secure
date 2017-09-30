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
    sudo docker-machine create --driver openstack \
      --openstack-auth-url "http://iamv3.savitestbed.ca:5000/v2.0" \
      --openstack-insecure \
      --openstack-flavor-name $VM_FLAVOR --openstack-image-name "Ubuntu-14-04" \
      --openstack-tenant-name "demo2" --openstack-region "CORE-2" \
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
