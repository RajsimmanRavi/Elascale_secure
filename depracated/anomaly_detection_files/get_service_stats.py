import json
from datetime import datetime
import os
import csv
import time
import warnings
warnings.filterwarnings("ignore")

DOCKBEAT_FILE="/tmp/dockbeat/dockbeat"

# Gets all the data from the directory of files
# Need service name to fetch only those data
def get_serv_data(line, serv_name):

    cpu_data = []
    network_rx_data = []

    # Get stats from all the files
    stats = []

    try:
        load_data = json.loads(line)
        if(any(d['value'] == serv_name for d in load_data["containerLabels"])):
            stats.append(load_data)
    except Exception as e:
        print("Found error on line: "+str(e))
        print("ignoring...")
        #continue

    for st in stats:
        #print(st)
        #if "net" in st and (str(st["net"]["name"]) == "eth1"):
        if st["type"] == "net" in st:
            net_data = "["+str(st["net"]["name"])+" RECEIVED PACKETS STATS]: "+st["@timestamp"]+","+str(st["net"]["rxPackets_ps"])
            print(net_data)
        elif st["type"] == "cpu" in st:
            data = "[CPU USAGE STATS]: "+st["@timestamp"]+","+str(st["cpu"]["totalUsage"])
            print(data)

    #return network_rx_data, cpu_data

def follow(thefile, serv_name):

    thefile.seek(0,2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(10)
            continue
        yield line

def parse_dockbeat(serv_name):
    logfile = open(DOCKBEAT_FILE, 'r')
    loglines = follow(logfile, serv_name)
    follow(DOCKBEAT_FILE, serv_name)

    for line in loglines:
        get_serv_data(line, serv_name)

if __name__=="__main__":
    parse_dockbeat("http_web")

