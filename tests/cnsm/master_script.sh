#!/bin/bash

APP="iot_app"
ELASCALE_LOG="/var/log/elascale/elascale.csv"
COMPOSE_FILE="/home/ubuntu/Elascale_secure/docker_compose/iot_app_compose.yml"

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
    # Remove old Autoscaler log file
    sudo rm $ELASCALE_LOG
    
    # Go to the Elascale_secure folder to start autoscaler
    cd /home/ubuntu/Elascale_secure
    
    # Start Elascale Autoscaler on tmux session
    tmux new -d -s manager "sudo python2.7 -m autoscaler.manager.main -p 'a' -ad True -ad_alg $1"

    sleep 10s
}

function start_tests {
    # Go to the tests folder
    cd /home/ubuntu/Elascale_secure/tests/cnsm
    
    # Start the test scaling
    echo "Start Scaling tests..."
    sudo ./edos_testing.sh "$1"
    
    # Copy CPU and replica stats from Elascale Autoscaler
    sudo cp $ELASCALE_LOG $2
}


for i in {1..1}
do
    rm_app 
    rm_autoscaler
    deploy_app
    
    start_autoscaler 'htm'
    start_tests "temporal" stats_temporal_htm.csv
    
    #if [ "$i" -eq 1 ];then
    #    start_autoscaler 're'
    #    start_tests "temporal" stats_temporal_re.csv
    #elif [ "$i" -eq 2 ];then
    #    start_autoscaler 'htm'
    #    start_tests "temporal" stats_temporal_htm.csv
    #fi
    
    
    rm_app
    rm_autoscaler

    sleep 120s
done
