import sys
import requests
import pycurl
import pprint
import json
import time
import autoscaler.network.setup_topology as setup_topo
import autoscaler.util as util
import autoscaler.conf.engine_config as eng
import autoscaler.network.network_util as net_util

def ovsdb_request(switch_dpid, switch_ip):

    ovsdb_data = 'tcp:'+switch_ip+':6632'
    data = json.dumps(ovsdb_data)
    ovsdb_url = 'http://'+eng.RYU_CONTROLLER+'/v1.0/conf/switches/'+str(switch_dpid)+"/ovsdb_addr"

    print(data)
    print(ovsdb_url)

    c = pycurl.Curl()
    c.setopt(pycurl.URL, ovsdb_url)
    c.setopt(pycurl.CUSTOMREQUEST, "PUT")
    c.setopt(pycurl.POSTFIELDS, '%s' % data)
    c.perform()

    #data = requests.put(ovsdb_url, json.dumps(ovsdb_data))
    #print data.text

# max_rate is the max ceil for the qos
# max_q_rate is the max ceil for that queue
def insert_qos(port, switch_dpid, min_rate):

    #queue_data = '{"port_name": "'+port+'", "type": "linux-htb", "max_rate": "10000000", "queues": [{"max_rate": "900000", "min_rate": "100000"}, {"max_rate": "9000000", "min_rate": "1000000"}]}'
    queue_data = '{"port_name": "'+port+'", '
    queue_data += '"type": "linux-htb", '
    queue_data += '"max_rate": "10000000", '
    queue_data += '"queues": [{"min_rate": "'+str(min_rate)+'"}]}'
    #queue_data += '"queues": [{"max_rate": "900000", "min_rate": "100000"}, {"max_rate": "9000000", "min_rate": "1000000"}]}'

    queue_url = 'http://'+eng.RYU_CONTROLLER+'/qos/queue/'+switch_dpid

    print(queue_url)
    print(queue_data)

    data = requests.post(queue_url, data = queue_data)

    print(data.text)


# For this, you definitely need OpenFlow13 for your main ovs bridge
def insert_qos_rule(ip_addr, port, queue_id, sw_dpid):

    qos_rule = '{"priority": 2, "match": {"nw_dst": "'+ip_addr+'", "nw_proto": "TCP", "tp_dst": "'+port+'"}, "actions":{"queue": "'+str(queue_id)+'"}}'
    qos_url = 'http://'+eng.RYU_CONTROLLER+'/qos/rules/'+sw_dpid

    data = requests.post(qos_url, data = qos_rule)
    print(data.text)

def delete_qos_queues():

    queue_url = 'http://'+eng.RYU_CONTROLLER+'/qos/queue/all'
    data = requests.delete(queue_url).json()

    for item in data:
        pprint.pprint(item)

    print("Deleted Queues...preparing for deleting QoS")
    time.sleep(5)

    qos_data = '{"qos_id": "all"}'
    qos_url = 'http://'+eng.RYU_CONTROLLER+'/qos/rules/all'

    c = pycurl.Curl()
    c.setopt(pycurl.URL, qos_url)
    c.setopt(pycurl.CUSTOMREQUEST, "DELETE")
    c.setopt(pycurl.POSTFIELDS, '%s' % qos_data)
    c.perform()
    """
    for item in data:
        pprint.pprint(item)
    """

def configure_switch(sw, port, dest_ip, min_rate):
    sw_ip =  (list(eng.IP_MAPPER.keys())[list(eng.IP_MAPPER.values()).index(sw)])
    sw_mac = net_util.get_dpid(sw_ip)

    print(sw_ip)
    print(sw_mac)

    # First Step
    ovsdb_request(sw_mac, sw_ip)

    # Second Step
    port = eng.PORT_MAPPER[sw]

    #print("SET OVSDB...waiting...")
    util.progress_bar(5)

    # Third Step
    insert_qos(port, sw_mac, min_rate)

    # Insert QoS Rule to throttle iperf traffic
    insert_qos_rule(dest_ip, "5201", 0, sw_mac)



def qos(src_ip, dest_ip, min_rate):

    # Before doing anything, delete old qos and queue rules
    delete_qos_queues()

    # First, get the switches in-between 2 hosts
    path = setup_topo.setup_and_find(src_ip, dest_ip)
    print(path)
    """
    For each switch, do the following:
        1. Setup OVSDB for the switch: curl -X PUT -d '"tcp:{$SWITCH_IP}:6632"' http://ryu_controller/v1.0/conf/switches/{$SWITCH_DPID}/ovsdb_addr
        2. Find the port connected to the host (Basically hard-coding for now): h1 -> pair_h2_1 -> pair_h3_1 -> pair_h1_1 -> h4
        3. Add queue to that port:
        curl -X POST -d \
        '{"port_name": "{$PORT}", "type": "linux-htb", "max_rate": "10000000", "queues": [{"max_rate": "7000000", "min_rate": "1000000"}]}' \
        http://ryu_controller/qos/queue/{$SWITCH_DPID}
    """

    for i in range(len(path)):
        if i != len(path)-1:
            port = get_port(path(i), path(i+1))
            if "sw" in path[i]:
                configure_switch(path(i), port, dest_ip, min_rate)
            if "sw" in path[i+1]:
                configure_switch(path(i+1), port, dest_ip, min_rate)



if __name__=="__main__":
    qos(sys.argv[1], sys.argv[2], sys.argv[3])
