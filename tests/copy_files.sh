#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 FILE_NAME" >&2
  exit 1
fi

rm $1

F_NAME="$1"

BASE_CMD="sudo docker-machine ssh iot-agg-sensor"

CONTAINER_ID=`$BASE_CMD "sudo docker ps | grep sensor | cut -d ' ' -f 1"`

COPY_TO_HOST=`$BASE_CMD "sudo docker cp $CONTAINER_ID:/usr/src/send_data/stats.csv $F_NAME"`

COPY_TO_MASTER=`sudo docker-machine scp iot-agg-sensor:~/$F_NAME $F_NAME`
