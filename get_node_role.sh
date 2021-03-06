#!/bin/bash

# This script is used to get the IP address of the node with specified label (given as argument)
# It is mainly used to figure out the IP address of the node with role='monitor' or role='master'
# node with role='monitor' is where Elasticsearch is running
# node with role='master' is where Elascale engine is running

# Check if arguments given
if [[ $# -ne 1 ]] ; then
    echo "Error: you need to provide the label role you're looking for"
    exit 1
fi

role="$1"

# First, find the SWARM NODES 

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
NODES=( $(sudo docker node ls --format '{{ .Hostname }}') )

for hostname in "${NODES[@]}"
do
    # Check each node whether it has a role 'monitor'
    node_role=`sudo docker node inspect $hostname | grep -w "$role"`

    # If the string is not empty, we found our node 
    if [ ! -z "$node_role" ];then

        # Now, get the IP address of that node
        # Remove all double quotes
        # Regex that IP address boi!
        # Get the one unique IP Address
        IP=`sudo docker node inspect $hostname | sed 's/"//g' | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | uniq`
        #echo "$IP"
        echo "$hostname:$IP"
    fi
done

