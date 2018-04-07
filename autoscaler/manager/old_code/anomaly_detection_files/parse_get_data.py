import json
from datetime import datetime
import os
import csv
from get_data_ad import detect_anomaly
import pandas as pd
import numpy as np
import util
import warnings
warnings.filterwarnings("ignore")

DOCKBEAT_DIR="/tmp/dockbeat"
DATASET_DIR="/tmp/anomaly_dataset/"

data_files = ["cpu_dataset.csv", "network_rx_dataset.csv"]

def write_to_file(f_name, data_list):
    f = open(f_name,'a')

    # Add Header
    f.write("Date,Value")
    f.write('\n')

    # Add data
    for line in data_list:
        if "0001-01-01T00" not in line:
            f.write(line)
            f.write('\n')

    f.close()

def delete_old_file(f_name):
    try:
        os.remove(f_name)
    except OSError:
        pass

# Gets all the data from the directory of files
# Need service name to fetch only those data
def get_all_data(dockbeat_dir, serv_name):

    cpu_data = []
    network_rx_data = []

    # Get stats from all the files
    stats = []

    files = os.listdir(dockbeat_dir)

    for f in files:
        for line in open(dockbeat_dir+"/"+f, 'r'):
            try:
                load_data = json.loads(line)
                if(any(d['value'] == serv_name for d in load_data["containerLabels"])):
                    stats.append(load_data)
            except Exception as e:
                #print("Found error on line: "+str(e))
                #print("ignoring...")
                continue

    for st in stats:
        if st["type"] == "net":
            data = st["@timestamp"]+","+str(st["net"]["rxPackets_ps"])
            network_rx_data.append(data)
        elif st["type"] == "cpu" in st:
            cpu_data.append(st["@timestamp"]+","+str(st["cpu"]["totalUsage"]))

    return network_rx_data, cpu_data

def sort_data(data_list):

    format = "%Y-%m-%dT%H:%M:%S.%fZ"
    sorted_lines = sorted(data_list, key=lambda line: datetime.strptime(line.split(",")[0], format))

    return sorted_lines

def parse_dockbeat(serv_name):

    for data_file in data_files:
        delete_old_file(DATASET_DIR+data_file)
        print("Deleted %s" % DATASET_DIR+data_file)

    network_rx_data, cpu_data = get_all_data(DOCKBEAT_DIR, serv_name)
    print("Got all Stats!!")

    # sort values
    network_rx_data = sort_data(network_rx_data)
    cpu_data = sort_data(cpu_data)


    # write to file
    write_to_file(DATASET_DIR+"cpu_dataset.csv", cpu_data)
    write_to_file(DATASET_DIR+"network_rx_dataset.csv", network_rx_data)

    #print("finished writing to files!")

    cpu_report = detect_anomaly(DATASET_DIR+"cpu_dataset.csv")
    net_rx_report = detect_anomaly(DATASET_DIR+"network_rx_dataset.csv")
    #report = "CPU REPORT: "+str(cpu_report)+"\nNETWORK REPORT: "+str(net_rx_report)

    """
    # Evaluate the signals
    if cpu_report == False and net_rx_report == False:
        print("Looks ok. Did not cross the difference of 0.45 or 1.0 for network")
        return False
    elif cpu_report != False and net_rx_report != False:
        print("Clearly somehting is off! Both signals point anomalies. Don't Autoscale!")
        return True
    else:
        print("One of the signlas point anomalies. Just ignore for now")
        return True
    """
if __name__=="__main__":

    #parse_dockbeat("http_web")

    while(1):
        parse_dockbeat("http_web")

        util.progress_bar(60)

