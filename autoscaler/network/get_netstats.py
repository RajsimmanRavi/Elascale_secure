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
import autoscaler.network.qos_rest as insert_qos

def init_port_db():
    db = Base('port_tracker.pdl', save_to_file=False)
    db.create('sw', 'port_name', 'byte_count')

    return db

def init_flow_db():
    db = Base('flow_tracker.pdl', save_to_file=False)
    db.create('sw', 'src', 'dst', 'byte_count')
    return db

def get_port_desc(dpid):
    port_dict = {}
    dpid = str(dpid)
    ryu_controller = eng.RYU_CONTROLLER
    url = 'http://'+ryu_controller+'/stats/portdesc/'+dpid
    data = requests.get(url).json()
    data = json.dumps(data) # Convert dict to json string
    data = json.loads(data) # Convert json string to json object

    for info in data[str(dpid)]:
        if "pair" in info["name"]:
            port_dict[info["name"]] = info["port_no"]

    #print(port_dict)
    return port_dict

def get_port_stats(dpid, switch, port_name, port_no, db):
    dpid = str(dpid)
    port_no = str(port_no)
    ryu_controller = eng.RYU_CONTROLLER
    url = 'http://'+ryu_controller+'/stats/port/'+dpid+'/'+port_no
    data = requests.get(url).json()
    data = json.dumps(data) # Convert dict to json string
    data = json.loads(data) # Convert json string to json object
    for stats in data[str(dpid)]:
        try:
            curr_byte_count = stats["tx_bytes"] # I'm taking TX_bytes beacuse of egree traffic
            prev = db(sw=switch, port_name=port_name)

            if len(prev) != 0:
                bw = net_util.calc_bw_left(prev[0]["byte_count"], curr_byte_count)
                db.delete(prev) # delete that record coz you don't care anymore
                # Insert/replace the record for bandwidth calculation next time
                r = db.insert(sw=switch,port_name=port_name,byte_count=curr_byte_count)
            else:
                db.delete(prev) # delete that record coz you don't care anymore
                # Insert/replace the record for bandwidth calculation next time
                r = db.insert(sw=switch,port_name=port_name,byte_count=curr_byte_count)
                print("First time...wait for another iteration")
                #print("entering zero...because of first time")
                raise ValueError("First Iteration, no comparison yet.")

        except Exception as e:
            traceback.print_exc()
            pass

        else:
            print("Switch: %s --> Port Name: %s ==> Bandwdith: %s " %(switch,port_name,net_util.bytes_2_human_readable_bits(bw)))

def get_flow_stats(dpid, switch, db):
    dpid = str(dpid)
    ryu_controller = eng.RYU_CONTROLLER
    url = 'http://'+ryu_controller+'/stats/flow/'+dpid
    data = requests.get(url).json()
    data = json.dumps(data) # Convert dict to json string
    data = json.loads(data) # Convert json string to json object

    for flow in data[str(dpid)]:
        #print(flow)
        try:
            src = eng.MAC_MAPPER[flow["match"]["dl_src"]]
            dst = eng.MAC_MAPPER[flow["match"]["dl_dst"]]
            curr_byte_count = flow["byte_count"]

            prev = db(sw=switch, src=src, dst=dst) # Get record matching that switch and flow
            #print(prev)
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
            #traceback.print_exc()
            pass

        else:

            print("Switch: %s --> Flow: %s to %s ==> Bandwdith: %s " %(switch,src,dst,net_util.bytes_2_human_readable_bits(bw)))

            if bw > (10000000/8):
                print("Uh oh...Throttle time!")
                src_ip = list(eng.IP_MAPPER.keys())[list(eng.IP_MAPPER.values()).index(src)]
                dest_ip = list(eng.IP_MAPPER.keys())[list(eng.IP_MAPPER.values()).index(dst)]
                max_rate = 2000000
                insert_qos.qos(src_ip, dest_ip, max_rate)

def main():


    flow_db = init_flow_db()
    port_db = init_port_db()

    switches = [eng.SW1_IP, eng.SW2_IP, eng.SW3_IP]

    bytes_stats = {}
    while(1):
        for sw in switches:
            dpid = int(net_util.get_dpid(sw),16)
            get_flow_stats(dpid, eng.IP_MAPPER[sw], flow_db)

            """
            port_dict = get_port_desc(dpid)
            for port_name, port_no in port_dict.items():
                get_port_stats(dpid, eng.IP_MAPPER[sw], port_name, port_no, port_db)
            """

        util.progress_bar(eng.MONITORING_INTERVAL)


if __name__=="__main__":
    main()
