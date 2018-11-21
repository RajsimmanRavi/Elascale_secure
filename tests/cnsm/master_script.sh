#!/bin/bash

APP="iot_app"
ELASCALE_LOG="/var/log/elascale/elascale.csv"
COMPOSE_FILE="/home/ubuntu/Elascale_secure/docker_compose/iot_app_compose.yml"
RE_STATS="/var/log/elascale/re_stats.csv"
HTM_STATS="/var/log/elascale/htm_stats.csv"

function rm_app {
    sudo docker stack rm $APP
    sleep 5s
}

function rm_autoscaler {
    PID=`ps -aux | grep autoscaler | grep tmux |  awk '{print $2}'`
    sudo kill -9 $PID 
}

function deploy_app { 
    sudo docker stack deploy -c $COMPOSE_FILE $APP

    # Waiting it to be stabilized (REST API takes a while)
    echo "Waiting for application to be stabilized..."
    sleep 180s
}

function start_autoscaler () {

    sudo rm $RE_STATS
    sudo rm $HTM_STATS

    echo "Starting Autoscaler..."

    # Remove old Autoscaler log file
    sudo rm $ELASCALE_LOG
    
    # Go to the Elascale_secure folder to start autoscaler
    cd /home/ubuntu/Elascale_secure

    if [ "$1" == "compare" ]; then
        # Start Elascale Autoscaler on tmux session with specific anaomaly detection algorithm
        tmux new -d "sudo python2.7 -m autoscaler.manager.main -p 'none' -ad True -ad_alg $2"
    else
        # Start Elascale Autoscaler on tmux session with/without anomaly detection and specific anaomaly detection algorithm
        tmux new -d -s manager "sudo python2.7 -m autoscaler.manager.main -p 'a' -ad $2 -ad_alg $3"
    fi
    
    sleep 10s
}

function start_tests {
    # Go to the tests folder
    cd /home/ubuntu/Elascale_secure/tests/cnsm
    
    # Start the test scaling
    echo "Start Scaling tests..."
    sudo ./edos_testing.sh "$1"
    
    # Copy CPU and replica stats from Elascale Autoscaler
    sudo cp $RE_STATS "/home/ubuntu/Elascale_secure/tests/cnsm/re_$1.csv"
    sudo cp $HTM_STATS "/home/ubuntu/Elascale_secure/tests/cnsm/htm_$1.csv"
}


function compare_htm_re {
    
rm_app 
rm_autoscaler
deploy_app


start_autoscaler "compare" 're'
#start_autoscaler "compare" 'htm'

start_tests "concept_drift" 

rm_app
rm_autoscaler
    

}

function measure_edos {
    

    rm_app 
    rm_autoscaler
    deploy_app
    start_autoscaler "edos" "True" "htm"
    start_tests "spatial" 
    rm_app
    rm_autoscaler

    #for i in {1..2}
    #do
    #    rm_app 
    #    rm_autoscaler
    #    deploy_app
    #    
    #    if [ "$i" -eq 1 ];then
    #        start_autoscaler "edos" "False" "htm"
    #        start_tests "concept_drift" edos_concept_drift_False.csv
    #    elif [ "$i" -eq 2 ];then
    #        start_autoscaler "edos" "True" "htm"
    #        start_tests "concept_drift" edos_concept_drift_True.csv
    #    fi
    #    
    #    
    #    rm_app
    #    rm_autoscaler
    #
    #    sleep 120s
    #done
}


if [ "$#" -ne 1 ]; then
  echo "Usage: $0 TEST TYPE(compare/edos_measure)" >&2
  exit 1
fi

if [ $1 = "compare" ]; then
  compare_htm_re
else
  measure_edos
fi
