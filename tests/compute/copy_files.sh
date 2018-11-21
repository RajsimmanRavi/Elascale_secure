#!/bin/bash

MACHINE="iot-agg-sensor"

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 FOLDER FILE_NAME" >&2
  exit 1
fi

FOLDER="$1"
F_NAME="$2"
rm $FOLDER/$F_NAME


BASE_CMD="sudo docker-machine ssh $MACHINE"

CONTAINER_ID=`$BASE_CMD "sudo docker ps | grep sensor | cut -d ' ' -f 1"`

COPY_TO_HOST=`$BASE_CMD "sudo docker cp $CONTAINER_ID:/usr/src/send_data/stats.csv $F_NAME"`

COPY_TO_MASTER=`sudo docker-machine scp $MACHINE:~/$F_NAME $FOLDER/$F_NAME`
