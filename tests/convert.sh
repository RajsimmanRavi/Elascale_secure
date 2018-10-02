#!/bin/bash

while read p; do
    epoch=`echo $p | awk '{print $1}'`
    converted=`date -d @$epoch +"%Y-%m-%d %R"`
    cpu=`echo $p | awk '{ print $2}'`
    minor_fault_sec=`echo $p | awk '{ print $3}'`
    mem=`echo $p | awk '{ print $4}'`
    echo "$converted,$cpu,$mem,$minor_fault_sec" 
done < $1

# I used this for conerting it into Military time (easier for vlookups in GSheets)
#while read p; do
#    date=`echo $p | awk -F ',' '{print $1}' | grep -v 'Time'`
#    converted=`date -d "$date AM +12 hour "`
#    echo $converted | awk '{print $1,$2, $3, $4}' 
#done < $1
