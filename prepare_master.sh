#!/bin/bash

HOSTNAME=`hostname`
UNAME_S=`uname -s` #Linux
UNAME_M=`uname -m` #x86_64

#directory you want to create (if it doesn't exist)
SCRIPTS_DIR="/home/ubuntu/Elascale_secure"

# Requirements file for install pip packages for Autoscaler Manager and UI
# RR: Not using pip3 as anomaly detection package nupic is available only in python2

# PIP3_AUTOSCALER_REQUIREMENTS="$SCRIPTS_DIR/autoscaler/pip3_requirements.txt" 
PIP2_AUTOSCALER_REQUIREMENTS="$SCRIPTS_DIR/autoscaler/pip2_requirements.txt"

#Remove the annoying 'sudo: unable to ...' warning 
sudo sed -i "s/127.0.0.1 .*/127.0.0.1 localhost $HOSTNAME/g" /etc/hosts

#Let's update first 
sudo apt-get update

#Install some prerequisite tools (if needed)
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

#Check if Docker is already installed
check_docker=`command -v docker`
if [ -z "$check_docker" ]
then 
    #Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

    #Add repository to install docker
    sudo add-apt-repository \
      "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) \
      stable"

    #Update to get latest versions
    sudo apt-get update

    #Finally, install docker-ce
    sudo apt-get -y install docker-ce

    #Check version
    echo "----- DOCKER VERSION -----"
    sudo docker version
else
    echo "Docker is already installed on this host!"
    sudo docker version
fi 


#********** Install docker-machine ****************

#Check if Docker is already installed
check_docker_machine=`command -v docker-machine`
if [ -z "$check_docker_machine" ]
then 
    #Download it and put it on the /us/local/bin folder for command access
    curl -L https://github.com/docker/machine/releases/download/v0.12.2/docker-machine-$UNAME_S-$UNAME_M >/tmp/docker-machine &&
    chmod +x /tmp/docker-machine &&
    sudo cp /tmp/docker-machine /usr/local/bin/docker-machine

    #Verify if downloaded successfully!
    echo "----- DOCKER-MACHINE VERSION -----"
    sudo docker-machine version
else 
    echo "Docker-machine is already installed on this machine"
    sudo docker-machine version
fi

#Initialize swarm and make the current node as swarm manager
sudo docker swarm init

#Let's Label this host as master
sudo docker node update --label-add role=master $HOSTNAME
#Check if SCRIPTS DIR exists. If not, fetch the scripts from the GitHub
if [ ! -d "$SCRIPTS_DIR" ]
then
    #********** Fetch the scripts from GitHub ****************
    sudo git clone https://github.com/RajsimmanRavi/Elascale_secure.git $SCRIPTS_DIR
    echo "Cloned scripts from Github repo"
    
    #Just to be sure, make chown ubuntu (not root) for SCRIPTS DIR directory
    sudo chown -R ubuntu:ubuntu $SCRIPTS_DIR 

    #********** Create certs directory for storing certificates ****************
    sudo mkdir $SCRIPTS_DIR/certs
    
    #Need to set logging file configuration. 
    sudo cp $SCRIPTS_DIR/config/daemon.json /etc/docker/

    #Need to restart docker
    sudo systemctl restart docker 
fi

#*********** Install elasticdump *************
check_elasticdump=`command -v elasticdump`
if [ -z "$check_elasticdump" ]
then
   #Get the latest version
   curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
   
   #Install nodejs
   sudo apt-get install -y nodejs
   
   #Install elasticdump
   sudo npm install elasticdump -g

   #check elasticdump version
   elasticdump_version=`elasticdump --version`
   echo "elasticdump version: $elasticdump_version"
else 

   echo "elasticdump is already installed on this host"

fi

#*********** Install htpasswd for Kibana UI Basic Authentication *************
check_htpasswd=`command -v htpasswd`
if [ -z "$check_htpasswd" ]
then
   # Get the Apache Utils 
   sudo apt-get install -y apache2-utils

   htpasswd_cmd=`command -v htpasswd`
   echo "htpasswd location: $htpasswd"
else 

   echo "htpasswd is already installed on this host"

fi


# RR: Heirarchical Temporal Memory utilizes python2 only. 
# Hence, installing packages for Autoscaler and UI using on pip2
sudo apt-get install -y python-pip
sudo pip2 install -r $PIP2_AUTOSCALER_REQUIREMENTS

#*********** Install pip and necessary packages for Autoscaler and UI ***************
#echo "---- INSTALLING PIP PACKAGES ----"
#sudo apt-get -y install python3-pip
#echo "---- UPGRADING PIP PACKAGE ----"
#sudo pip3 install --upgrade pip
#echo "---- INSTALLING AUTOSCALER PACKAGES ----"

echo "Everything is set. Now, you can start creating the platform for application development"
