#!/bin/bash

MACHINE="iot-agg-sensor"

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 FOLDER" >&1
  exit 1
fi

FOLDER="$1"
F_NAME="sensor"
#rm $FOLDER/*


BASE_CMD="sudo docker-machine ssh $MACHINE"
CONTAINERS=($($BASE_CMD "sudo docker ps | grep sensor | cut -d ' ' -f 1"))

for i in "${CONTAINERS[@]}"
do
    COPY_TO_HOST=`$BASE_CMD "sudo docker cp $i:/usr/src/send_data/stats.csv $F_NAME_$i"`
    COPY_TO_MASTER=`sudo docker-machine scp $MACHINE:~/$F_NAME_$i $FOLDER/$F_NAME_$i`
done

