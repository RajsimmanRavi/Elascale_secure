#!/bin/bash

APP="iot_app"
ELASCALE_LOG="/var/log/elascale/elascale.csv"
COMPOSE_FILE="/home/ubuntu/Elascale_secure/docker_compose/iot_app_compose.yml"
PERIOD=1200

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
    tmux new -d -s manager "sudo python2.7 -m autoscaler.manager.main -ad False -p '$1'"

    sleep 10s
}

function start_tests {
    # Go to the tests folder
    cd /home/ubuntu/Elascale_secure/tests
    
    # Monitor the replicas on background
    echo "Start Monitoring replicas..."
    sudo ./monitor_stats.sh $1 $PERIOD replicas & 
    
    # Start the test scaling
    echo "Start Scaling tests..."
    sudo ./test_scaling.sh
    
    # Copy the stats files here
    echo "Copy stats file here"
    sudo ./copy_files.sh $2
    
    # Copy CPU and replica stats from Elascale Autoscaler
    sudo cp $ELASCALE_LOG $3
}

rm_autoscaler
start_autoscaler a
cd /home/ubuntu/Elascale_secure/tests
start_tests "replicas_5.csv" "stats_5.csv" "elascale_5.csv"
rm_autoscaler


#for i in {1..3}
#do
#    rm_app 
#    rm_autoscaler
#    deploy_app
#    if [ "$i" -eq 2 ];then
#        start_autoscaler d
#    elif [ "$i" -eq 3 ];then
#        start_autoscaler a
#    fi
#    start_tests "replicas_$i.csv" "stats_$i.csv" "elascale_$i.csv"
#    rm_app
#    rm_autoscaler
#
#    sleep 120s
#done