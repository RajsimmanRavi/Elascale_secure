#!/bin/bash

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 FILE_NAME DURATION (secs) TYPE (replicas/process_cpu/host_cpu)" >&2
  exit 1
fi

rm $1

function monitor_replicas() {
    echo "Time,Sensor_replicas,REST_API_replicas" >> $1
    
    START=`date +%s`
    while [ $(( $(date +%s) - $2 )) -lt $START ]; do  
    
      sensor_replicas=`sudo docker service ls --filter name=iot_app_sensor --format '{{ .Replicas }}' | awk -F '/' '{print $1}'`
      rest_replicas=`sudo docker service ls --filter name=iot_app_rest_api --format '{{ .Replicas }}' | awk -F '/' '{print $1}'`
      NOW=$(date +"%Y-%m-%d %R")
      echo "$NOW,$sensor_replicas,$rest_replicas" >> $1
    
      sleep 30 
    
    done
}

function monitor_host_cpu() {
    echo "Time,Host CPU usage" >> $1
    
    START=`date +%s`
    while [ $(( $(date +%s) - $2 )) -lt $START ]; do  
    
      total_cpu=`grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage "%"}'`
      NOW=$(date +"%Y-%m-%d %R")
      echo "$NOW,$total_cpu" >> $1
    
      sleep 1
    
    done
}

function monitor_process_cpu() {
    PID=`ps -aux | grep autoscaler | grep -v "sudo\|grep" | awk '{print $2}'`

    pidstat -hru -p $PID 1 $2 | grep -v "CPU" >> $1

    # remove empty lines
    awk 'NF' $1 | awk '{print $1, $7, $9, $13}' >> tmp.csv

    # Move temp data back to original name
    mv tmp.csv $1

    # Adding header to a new temp file (later will be renamed)
    echo "Time,CPU usage,Memory usage,Minor Faults/sec" >> tmp.csv
    
    # Convert epoch into human readable time and make it into csv
    ./convert.sh $1 >> tmp.csv

    # Move temp data back to original name
    mv tmp.csv $1
}

if [[ "$3" == "replicas" ]]; then
    monitor_replicas $1 $2 
elif [[ "$3" == "host_cpu" ]]; then
    monitor_host_cpu $1 $2
else
    monitor_process_cpu $1 $2
fi
