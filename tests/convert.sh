#!/bin/bash

while read p; do
    date=`echo $p | awk -F ',' '{print $1}' | grep -v 'Time'`
    converted=`date -d "$date AM +12 hour "`
    echo $converted | awk '{print $1,$2, $3, $4}' 
done < replicas_3.csv
