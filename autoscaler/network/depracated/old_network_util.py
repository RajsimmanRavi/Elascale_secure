import requests
import autoscaler.conf.engine_config as eng
import os

def remove_old_create_new(f_name, header):
    if os.access(f_name, os.R_OK):
        os.remove(f_name)
        write_to_file(header, f_name)

def write_to_file(stats, f_name):
    csv = open(f_name, "a")
    csv.write(stats)

def get_dpid(ip):
    ryu_controller = eng.RYU_CONTROLLER
    url = 'http://'+ryu_controller+'/v1.0/topology/switches'
    data = requests.get(url).json()
    for item in data:
        if ip == item["ip"]:
            return item["dpid"]

def calc_bw(prev, curr):
    prev = float(prev)
    curr = float(curr)

    bw = ((curr - prev)/eng.MONITORING_INTERVAL)
    return bw

def calc_bw_left(prev, curr):
    bw = calc_bw(prev, curr)
    max_bw = 125000000  #500000000 Bits

    bw_left = max_bw - bw
    return bw_left

# Reference: https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb/37423778
def bytes_2_human_readable_bits(number_of_bytes):
    if number_of_bytes < 0:
        raise ValueError("!!! number_of_bytes can't be smaller than 0 !!!")

    step_to_greater_unit = 1000.

    number_of_bits = float(number_of_bytes)*8
    unit = 'bits/s'

    if (number_of_bits / step_to_greater_unit) >= 1:
        number_of_bits /= step_to_greater_unit
        unit = 'Kb/s'

    if (number_of_bits / step_to_greater_unit) >= 1:
        number_of_bits /= step_to_greater_unit
        unit = 'Mb/s'

    if (number_of_bits / step_to_greater_unit) >= 1:
        number_of_bits /= step_to_greater_unit
        unit = 'Gb/s'

    if (number_of_bits / step_to_greater_unit) >= 1:
        number_of_bits /= step_to_greater_unit
        unit = 'Tb/s'

    number_of_bits = "%.3f" % number_of_bits

    return str(number_of_bits) + ' ' + unit


# Keeping this for namesake.... remove after
def get_port_stats(dpid):

    dpid = str(dpid)
    ryu_controller = eng.RYU_CONTROLLER
    url = 'http://'+ryu_controller+'/stats/port/'+dpid
    data = requests.get(url).json()
    #print(json.dumps(data, indent=4, sort_keys=True))
    data = json.dumps(data) # Convert dict to json string
    data = json.loads(data) # Convert json string to json object

    rx_bytes = 0
    for ports in data[str(dpid)]:
        rx_bytes += float(ports["rx_bytes"])

    #print("For Switch: %s, total Rx Bytes: %s" %(dpid, str(rx_bytes)))
    return rx_bytes

