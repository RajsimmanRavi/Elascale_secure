#!/bin/bash

CONFIG_FILE="/home/ubuntu/Elascale_secure/autoscaler/conf/engine_config.py"
NODES=( $(sudo docker node ls --format '{{ .Hostname }}') )

for hostname in "${NODES[@]}"
do
    # eg. hostname: iot-rajsimman-h1 ... we want to get only 'h1'
    IFS='-' read -ra NAME <<< "$hostname"
    name_id="${NAME[2]}"
    mac=`sudo docker-machine ssh $hostname cat /sys/class/net/p0/address`
    if [[ -z $mac ]]; then
      mac=`cat /sys/class/net/p0/address`
    fi
    
    echo "$name_id: $mac"

    sed -i "s/\".*\": \"$name_id\",/\"$mac\": \"$name_id\",/g" $CONFIG_FILE


done

