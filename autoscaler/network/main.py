import sys
import traceback
import requests
import json
import pprint
from pydblite import Base
import autoscaler.util as util
from collections import defaultdict
import autoscaler.conf.engine_config as eng
import autoscaler.network.network_util as net_util
import autoscaler.network.qos_rest as rest_qos
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from pytz import timezone
import argparse

parser = argparse.ArgumentParser(description="*** Elascale Network Autoscaler Arguments ***")
parser.add_argument('-m', '--monitor', help='Enable Monitor Mode? Does not enforce QoS, provides just stats (arg: bool). Default: False', type=util.str2bool, nargs='?', default=False)
args = parser.parse_args()

iot_file = "/home/ubuntu/Elascale_secure/autoscaler/network/iot_stats.csv"
iperf_file = "/home/ubuntu/Elascale_secure/autoscaler/network/iperf_stats.csv"

net_util.remove_old_create_new(iot_file, "Time, IoT Application Bandwidth\n")
net_util.remove_old_create_new(iperf_file, "Time, Iperf Application Bandwidth\n")

def init_port_db():
    db = Base('port_tracker.pdl', save_to_file=False)
    db.create('sw', 'port_name', 'byte_count')

    return db

def init_flow_db():
    db = Base('flow_tracker.pdl', save_to_file=False)
    db.create('sw', 'src', 'dst', 'byte_count')
    return db

def monitor_flow_stats(dpid, switch, db):

    # This is for evaluation purposes
    fmt = '%Y-%m-%d %H:%M'
    eastern = timezone('US/Eastern')

    dpid = str(dpid)
    #print("Switch: %s DPID: %s"% (str(switch), dpid))
    ryu_controller = eng.RYU_CONTROLLER
    url = 'http://'+ryu_controller+'/stats/flow/'+dpid
    data = requests.get(url).json()
    data = json.dumps(data) # Convert dict to json string
    print(data)
    data = json.loads(data) # Convert json string to json object

    for flow in data[str(dpid)]:
        #print(flow)
        try:
            src = eng.MAC_MAPPER[flow["match"]["dl_src"]]
            dst = eng.MAC_MAPPER[flow["match"]["dl_dst"]]
            curr_byte_count = flow["byte_count"]

            prev = db(sw=switch, src=src, dst=dst) # Get record matching that switch and flow
            if len(prev) != 0:
                bw = net_util.calc_bw(prev[0]["byte_count"], curr_byte_count)
                db.delete(prev) # delete that record coz you don't care anymore
                # Insert/replace the record for bandwidth calculation next time
                r = db.insert(sw=switch,src=src,dst=dst,byte_count=curr_byte_count)
            else:
                #print("entering zero...because of first time")
                #bw = net_util.calc_bw(0, curr_byte_count)
                db.delete(prev) # delete that record coz you don't care anymore
                # Insert/replace the record for bandwidth calculation next time
                r = db.insert(sw=switch,src=src,dst=dst,byte_count=curr_byte_count)
                print("First Iteration, no comparsion yet.")
                raise ValueError("First Iteration, no comparsion yet.")

        except Exception as e:
            #print("Error")
            #traceback.print_exc()
            pass

        else:

            print("Switch: %s --> Flow: %s to %s ==> Bandwdith: %s " %(switch,src,dst,net_util.bytes_2_human_readable_bits(bw)))

            # This is for collecting stats for evaluation
            time_stamp = datetime.now(eastern).strftime(fmt)
            net_stats = "%s,%s\n" %(time_stamp, str(bw*8))
            if (switch == "sw_1" and src == "h5" and dst == "h2"):
                net_util.write_to_file(net_stats, iot_file)
            if (switch == "sw_1" and src == "h6" and dst == "h7"):
                net_util.write_to_file(net_stats, iperf_file)

            enable_monitor = args.monitor
            if enable_monitor == False:
                if (bw*8) > eng.MAX_BW:
                    print("---> Uh oh...Throttle time! <--- \n")
                    src_ip = list(eng.IP_MAPPER.keys())[list(eng.IP_MAPPER.values()).index(src)]
                    dest_ip = list(eng.IP_MAPPER.keys())[list(eng.IP_MAPPER.values()).index(dst)]
                    max_rate = eng.MIN_BW
                    rest_qos.qos(src_ip, dest_ip, max_rate)

def main():

    print(util.run_command("figlet -f big Elascale Network"))
    print(util.run_command("python2.7 -m autoscaler.network.main -h"))

    flow_db = init_flow_db()
    port_db = init_port_db()

    print("\n\n---> Deleting any old QoS rules/policies...\n")
    switches = [eng.SW1_IP, eng.SW2_IP, eng.SW3_IP]
    rest_qos.delete_qos(switches)
    print("\n\n---> Cleaned table! Moving onto monitoring flows...\n")
    while(1):
        for sw in switches:
            dpid = int(net_util.get_dpid(sw),16)
            monitor_flow_stats(dpid, eng.IP_MAPPER[sw], flow_db)

        util.progress_bar(eng.MONITORING_INTERVAL)


if __name__=="__main__":
    main()
