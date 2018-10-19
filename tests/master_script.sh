#!/bin/bash

APP="iot_app"
ELASCALE_LOG="/var/log/elascale/elascale.csv"
COMPOSE_FILE="/home/ubuntu/Elascale_secure/docker_compose/iot_app_compose.yml"
EVAL_1_PERIOD=1200 # For Eval_1
EVAL_1_FOLDER="eval_1" # folder to store stats 

EVAL_2_PERIOD=300  # For Eval_2
EVAL_2_FOLDER="eval_2" # folder to store stats 

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
    sudo ./monitor_stats.sh $1 $EVAL_1_PERIOD replicas & 
    
    # Start the test scaling
    echo "Start Scaling tests..."
    sudo ./test_scaling.sh "$4"
    
    # Copy the stats files here
    echo "Copy stats file here"
    sudo ./copy_files.sh $EVAL_1_FOLDER $2
    
    # Copy CPU and replica stats from Elascale Autoscaler
    sudo cp $ELASCALE_LOG $3
}

# This is what I did for Evaluation #1
for i in {1..2}
do
    rm_app 
    rm_autoscaler
    deploy_app
    if [ "$i" -eq 1 ];then
        start_autoscaler 'none'
    elif [ "$i" -eq 2 ];then
        start_autoscaler 'd'
    fi
    start_tests "$EVAL_1_FOLDER/replicas_$i.csv" "stats_$i.csv" "$EVAL_1_FOLDER/elascale_$i.csv" 'simple'
    rm_app
    rm_autoscaler

    sleep 120s
done

# This is what I did for Elavulation #2 (For Discrete vs. Adaptive Policies)
#for i in {1..2}
#do
#    rm_app 
#    rm_autoscaler
#    deploy_app
#    if [ "$i" -eq 1 ];then
#        start_autoscaler 'd'
#    elif [ "$i" -eq 2 ];then
#        start_autoscaler 'a'
#    fi
#        start_tests "$FOLDER/replicas_$i.csv" "stats_$i.csv" "$FOLDER/elascale_$i.csv" 'spatial'
#    rm_app
#    rm_autoscaler
#
#    sleep 120s
#done
