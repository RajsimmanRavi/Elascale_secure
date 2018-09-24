#!/bin/bash

HOSTNAME=`hostname`
UNAME_S=`uname -s` #Linux
UNAME_M=`uname -m` #x86_64

#Variables needed for keypair creation for Elascale engine log into swarm-master
#It uses ssh to login and execute scaling commands
PASS_KEY_DIR="/home/ubuntu/Elascale/pass_key"
PASS_KEY_FILE="pass_key"
PASSPHRASE="Elascale_to_swarm_master"

#directory you want to create (if it doesn't exist)
SCRIPTS_DIR="/home/ubuntu/Elascale"

#Remove the annoying 'sudo: unable to ...' warning 
sudo sed -i "s/127.0.0.1 .*/127.0.0.1 localhost $HOSTNAME/g" /etc/hosts

#Let's update first 
sudo apt-get update

#Install some prerequisite tools (if needed)
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

#Check if Docker is already installed
docker_version=`sudo docker version | grep "Version"`

if [ -z "$docker_version" ]
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
docker_machine_version=`sudo docker-machine version | grep "version"`

if [ -z "$docker_machine_version" ]
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

if [ ! -d "$SCRIPTS_DIR" ]
then
    #********** Create Elascale directory and fetch the scripts ****************
    sudo mkdir $SCRIPTS_DIR
    echo "Created Scripts directory at /home/ubuntu/Elascale"
fi

#Check is scripts is installed on the machine from github

if [ ! -f $SCRIPTS_DIR"/create_nodes.sh" ]
then 
    sudo git clone https://github.com/RajsimmanRavi/Elascale_scripts.git $SCRIPTS_DIR
    echo "Cloned scripts from Github repo"
fi

#*********** Install elasticdump *************
check_elasticdump=`elasticdump --version`

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

#Just to be sure, make chown ubuntu (not root) for Elascale directory
sudo chown -R ubuntu:ubuntu $SCRIPTS_DIR 

#************ Create SSH KEYPAIR for Elascale Engine to log into swarm-master for performing scaling commands

if [ ! -d "$PASS_KEY_DIR" ] 
then 
    #create the dir
    mkdir $PASS_KEY_DIR
    echo "Created Pass_key directory at $PASS_KEY_DIR"

    #Create the keypair. Kept the Email address empty
    ssh-keygen -t rsa -f $PASS_KEY_DIR/$PASS_KEY_FILE -P $PASSPHRASE -C ""

    #Add the pub key to authorized keys
    cat $PASS_KEY_DIR/$PASS_KEY_FILE.pub >> /home/ubuntu/.ssh/authorized_keys

    #Add the passphrase to txt file 
    echo "$PASSPHRASE" >> "$PASS_KEY_DIR/$PASS_KEY_FILE"_passphrase.txt

    echo "Created keypair configuration for Elascale Engine!"
else 
    echo "$PASS_KEY_DIR has been already created. Skipping keypair configuration..."
fi

echo "Everything is set. Now, you can start creating the platform for application development"
