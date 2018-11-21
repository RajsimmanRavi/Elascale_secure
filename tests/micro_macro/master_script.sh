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
    tmux new -d -s manager "sudo python2.7 -m autoscaler.manager.main -ad False -p 'a' -macro True"
    #tmux new -d -s manager "sudo python2.7 -m autoscaler.manager.main -ad False -p 'none' -macro True"

    sleep 10s
}

function start_tests {
    # Go to the tests folder
    cd /home/ubuntu/Elascale_secure/tests/micro_macro
    
    # Monitor the replicas on background
    #echo "Start Monitoring replicas..."
    #sudo ./get_replicas.sh & 
    
    # Start the test scaling
    echo "Start Scaling tests..."
    sudo ./test_scaling.sh 
    
    # Copy CPU and replica stats from Elascale Autoscaler
    sudo cp $ELASCALE_LOG .
}

rm_app 
rm_autoscaler

deploy_app
start_autoscaler
start_tests

rm_app
rm_autoscaler

