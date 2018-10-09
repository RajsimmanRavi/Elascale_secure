#!/bin/bash

DOCKER_MACHINE_CMD="sudo docker-machine ssh iot-rajsimman-h5"
SENSOR_DIR="/home/ubuntu/iot_app_ams/sensor"
REG_PERIOD=60
PERF_PERIOD=120

function rm_autoscaler {
    PID=`ps -aux | grep autoscaler | grep tmux |  awk '{print $2}'`
    sudo kill -9 $PID 
    sleep 5s
}

function rm_sensor {
    PID=`$DOCKER_MACHINE_CMD ps -aux | grep send_wifi_data | grep tmux |  awk '{print $2}'`
    $DOCKER_MACHINE_CMD sudo kill -9 $PID
}

function start_sensor { 
    $DOCKER_MACHINE_CMD tmux new -d -s sensor "python3.5 $SENSOR_DIR/send_wifi_data.py"

    # Waiting it to be stabilized
    echo "Waiting for sensor to be stabilized..."
    sleep 5s
}

function start_autoscaler () {
    # Go to the Elascale_secure folder to start autoscaler
    cd /home/ubuntu/Elascale_secure
    
    # Start Elascale Autoscaler on tmux session
    tmux new -d -s manager "sudo python2.7 -m autoscaler.network.main -m $1"

    sleep 10s
}

function start_tests {
    echo "Performing Iperf Tests for $PERF_PERIOD secs..."
    sudo docker-machine ssh iot-rajsimman-h6 tmux new -d -s iperf "iperf -c 192.168.200.16 --port 5201 -t $PERF_PERIOD -i 5"
    sleep $PERF_PERIOD
}

function copy_files {
    F_NAME="$SENSOR_DIR/stats.csv"
    COPY_TO_MASTER=`sudo docker-machine scp iot-rajsimman-h5:$F_NAME $1`
    cp /home/ubuntu/Elascale_secure/autoscaler/network/iot_stats.csv $2
    cp /home/ubuntu/Elascale_secure/autoscaler/network/iperf_stats.csv $3
}

function monitor_reg_flows {
    echo "Monitoring regular flows for $REG_PERIOD secs..."
    sleep $REG_PERIOD
}


for i in {1..2}
do
    rm_sensor
    rm_autoscaler
    
    start_sensor
    if [ "$i" -eq 1 ];then
        start_autoscaler True
    else
        start_autoscaler False
    fi
    
    cd /home/ubuntu/Elascale_secure/tests/network
    monitor_reg_flows 
    start_tests 
    echo "Done Tests. Going back to Regular period..."
    monitor_reg_flows 
    echo "Cleaning up and fetching stats files..."
    
    rm_sensor
    rm_autoscaler
    
    copy_files "stats_$i.csv" "iot_stats_$i.csv" "iperf_stats_$i.csv"
    
    sleep 10s
done
