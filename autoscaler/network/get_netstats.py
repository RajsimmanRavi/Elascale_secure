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

def init_db():
    db = Base('tracker.pdl', save_to_file=False)
    db.create('sw', 'src', 'dst', 'byte_count')
    return db

def get_flow_stats(dpid, switch, db):
    dpid = str(dpid)
    ryu_controller = eng.RYU_CONTROLLER
    url = 'http://'+ryu_controller+'/stats/flow/'+dpid
    data = requests.get(url).json()
    data = json.dumps(data) # Convert dict to json string
    data = json.loads(data) # Convert json string to json object

    for flow in data[str(dpid)]:
        try:
            src = eng.MAC_MAPPER[flow["match"]["dl_src"]]
            dst = eng.MAC_MAPPER[flow["match"]["dl_dst"]]
            curr_byte_count = flow["byte_count"]

            prev = db(sw=switch, src=src, dst=dst) # Get record matching that switch and flow
            #print(prev)
            if len(prev) != 0:
                bw = net_util.calc_bw(prev[0]["byte_count"], curr_byte_count)
            else:
                #print("entering zero...because of first time")
                bw = net_util.calc_bw(0, curr_byte_count)

            db.delete(prev) # delete that record coz you don't care anymore

            # Insert/replace the record for bandwidth calculation next time
            r = db.insert(sw=switch,src=src,dst=dst,byte_count=curr_byte_count)
        except Exception as e:
            #traceback.print_exc()
            pass

        else:
            print("Switch: %s --> Flow: %s to %s ==> Bandwdith: %s " %(switch,src,dst,net_util.bytes_2_human_readable_bits(bw)))

def main():


    db = init_db()
    switches = [eng.SW1_IP, eng.SW2_IP, eng.SW3_IP]

    bytes_stats = {}
    while(1):
        for sw in switches:
            dpid = int(net_util.get_dpid(sw),16)
            get_flow_stats(dpid, eng.IP_MAPPER[sw], db)
        util.progress_bar(eng.MONITORING_INTERVAL)


if __name__=="__main__":
    main()
