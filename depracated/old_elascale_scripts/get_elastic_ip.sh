#!/bin/bash

# We need to figure out the host where Elasticsearch is going to be deployed
# It is deployed in the node that contains the labels.role = 'elascale'

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
NODES=( $(sudo docker node ls | awk '{print $2}' | sed 's/*//g' | sed 's/Ready//g' |sed 's/HOSTNAME//g' | sed 's/STATUS//g'| sed '/^$/d') )

for hostname in "${NODES[@]}"
do
    # Check each node whether it has a role 'elascale'
    elascale_role=`sudo docker node inspect $hostname | grep -w "elascale"`

    # If the string is not empty, we found our node 
    if [ ! -z "$elascale_role" ];then

        #Now, get the IP address of that node
        #grep $hostname - get the node from docker-machine command (this contains the IP address info)
        #awk '{print $5}' - prints the ip address info tcp://x.x.x.x:2376
        #sed -e 's/tcp:\/\/\(.*\):2376/\1/'` tcp:_escape_fwd_slash_with_back_slash(get_this_string):2376
        #\1 tells get only 1 string. There is back_slash_for_open_and_close_brackets as well
        ELASTIC_IP=`sudo docker-machine ls | grep $hostname | awk '{print $5}' | sed -e 's/tcp:\/\/\(.*\):2376/\1/'`

        echo "$ELASTIC_IP"
    fi
done

