import os
import sys
import re
import json
import subprocess as sp
import time
from tqdm import tqdm
from prettytable import PrettyTable
import configparser
import autoscaler.conf.engine_config as eng
#import paramiko # not needed anymore

def run_command(command):
    p = sp.Popen(command, shell=True, stdout=sp.PIPE)
    output, err = p.communicate()

    return output

def get_util_info(service, curr_util, config):
    """ Fetches the current utilization  along with high and low thresholds defined in config file.

    Args:
        service: name of the service
        curr_util: the current utilization data of all services
        config: config file

    Returns:
        Dictionary of data:
            result = {
                "service" : xx,
                "curr_cpu_util" : xx,
                "curr_mem_util" : xx,
                "high_cpu_threshold" : xx,
                "low_cpu_threshold" : xx,
                "high_mem_threshold" : xx,
                "low_mem_threshold" : xx
            }
    """
    result = {}
    result["service"] = service
    result["curr_cpu_util"] = "%.3f " % curr_util[service]['cpu'] # Round it to 3 decimal digits
    result["curr_mem_util"] = "%.3f " % curr_util[service]['memory'] # Round it to 3 decimal digits
    result["curr_netRx_util"] = "%.3f " % curr_util[service]['netRx'] # Round it to 3 decimal digits
    result["curr_netTx_util"] = "%.3f " % curr_util[service]['netTx'] # Round it to 3 decimal digits
    result["high_cpu_threshold"] = config.get(service, 'cpu_up_lim') # Ex second argument should be: cpu_up_lim
    result["low_cpu_threshold"] = config.get(service, 'cpu_down_lim') # Ex second argument should be: cpu_low_lim
    result["high_mem_threshold"] = config.get(service, 'mem_up_lim') # Ex second argument should be: cpu_up_lim
    result["low_mem_threshold"] = config.get(service, 'mem_down_lim') # Ex second argument should be: cpu_low_lim

    return result

# Read config file
def read_config_file(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

# Write to config file
def write_config_file(f_name, mode, config_data):
    with open(f_name, mode) as f:
        config_data.write(f)
    return config_data

# Progress bar for our Time interval waiting to show how much time to wait
def progress_bar(time_interval):
    print("Wait for %s secs" % time_interval)
    for i in tqdm(range(time_interval)):
        time.sleep(1)

def pretty_print(service_type, data):
    """ Pretty prints Utilization of Micro/macroservice on terminal/docker logs

    Args:
        service_type: 'Micro' or 'Macro' keyword for printing on column header
        data: Dictionary of utilization data (get more info on get_util_info() function)
    """
    service = data["service"]
    curr_cpu = data["curr_cpu_util"]
    curr_mem = data["curr_mem_util"]
    curr_netTx = data["curr_netTx_util"]
    curr_netRx = data["curr_netRx_util"]
    high_cpu = data["high_cpu_threshold"]
    low_cpu = data["low_cpu_threshold"]
    high_mem = data["high_mem_threshold"]
    low_mem = data["low_mem_threshold"]

    x = PrettyTable()
    x.field_names = [service_type+"service", low_cpu+" < CPU < "+high_cpu, low_mem+" < Memory < "+high_mem, "Network Tx Bytes", "Network Rx Bytes"]
    x.add_row([service, curr_cpu, curr_mem, curr_netTx, curr_netRx])

    print(x)

    x.clear_rows()
    x.clear()

def compute_trajectory(cpu_status, mem_status):
    """ Function to alert whether mutliple resources are crossing thresholds or not.

    Args:
        cpu_status: Keyword 'High', 'Normal' or 'Low' mentioning the status of cpu
        mem_status: Keyword 'High', 'Normal' or 'Low' mentioning the status of memory

    Returns:
        status: Keyword 'High', 'Normal' or 'Low' mentioning the status of the resources
    """
    if cpu_status == "High" and mem_status == "High":
        return "High"
    elif cpu_status == "Low" and mem_status == "Low":
        return "Low"
    else:
        return "Normal"

def check_threshold(service, config_high_threshold, config_low_threshold, curr_util):
    """ Checks whether Utilization crossed discrete threshold

    Args:
        service: Name of the micro/macroservice
        config_high_threshold: Upper limit threshold to utilization set in config file
        config_low_threshold: Lower limit threshold to utilization set in config file
        curr_util: value of the current utilization

    Returns:
        String "High" if upper limit crossed
        String "Low" if lower limit crossed
        String "Normal" if none crossed
    """

    if float(curr_util) > float(config_high_threshold):
        return "High"
    elif float(curr_util) < float(config_low_threshold):
        return "Low"
    else:
        return "Normal"


# HK: Function that finds the latest added machine for that macroservice
# Param: base name of the macroservice (eg. iot-edge from the name: iot-edge.20170725)
# Returns: the entire name of the latest added node (i.e. iot-edge.20170725)
def find_candidate_instance_to_remove(base_name):

    vm_names = []
    result = run_command("sudo docker node ls")
    words = result.replace("\\", " ").replace("\n", " ").split(" ")

    for word in words:
        if word.__contains__(base_name):
            vm_names.append(word)
    if vm_names.__len__() > 0:
        vm_names.sort(reverse=True)
        return vm_names[0]  # return the instance that had been added lately.
    else:
        return ''

# HK: Get the labels given a specific node
# Param: node name
# Returns: label(s) of that name (eg. loc=edge)
def get_labels(node_name):
    node_info = run_command("sudo docker node inspect "+node_name)
    node_json = json.loads(node_info, encoding='utf8')
    if str(node_json[0]['Spec']).__contains__('Labels'):
        labels = dict(node_json[0]['Spec']['Labels'])
        return labels
    else:
        return ''

# RR: This function gets the name of the node that has the microservices running
# Param: name of the microservice
# Returns: the name of the macroservice that hosts that specific microservice
def get_macroservice(microservice):
    result = run_command("sudo docker service ps "+microservice)

    # The result will contain the line that has the node name
    label_line = re.search('iot-(.*)', result).group(1)

    # split the line to get only the node name
    macroservice = "iot-"+label_line.split(" ")[0]

    return macroservice

# RR: This function fetches the error status (if any) of the macroservice
# This is mainly used when creating a vm (or macroservice)
def check_macroservice_status(vm_name):
    result = run_command("sudo docker-machine ls")

    # split by newline
    vms = result.split("\n")

    # Ref: https://stackoverflow.com/questions/4843158/check-if-a-python-list-item-contains-a-string-inside-another-string
    # I basically use some fancy way to filter out the elements that contain any errors
    # If none found, I return empty []
    filters = ["Unknown", "Timeout"]
    error = [ x for x in vms if any(xx in x for xx in filters)]

    return error

# HK: This function gets the token in order for the node to join as a worker.
# It also fetches the swarm master's IP address
# Param: -
# Returns: worker token and the swarm master IP address
def get_token_and_master_ip_port():
    result = run_command("sudo docker swarm join-token worker")
    words = result.replace("\\", " ").replace("\n", " ").split(" ")
    token_index = words.index("--token") + 1

    token = words[token_index]
    master_ip_port = words[-3]
    return token, master_ip_port

# HK: This function gets the number of replicas for a given specific service at that point
# Param: service name
# Returns: the number of replicas for the given specific service
def get_micro_replicas(service_name):
    service_info = run_command("sudo docker service inspect "+service_name)
    service_json = json.loads(service_info, encoding='utf8')
    current_replicas = int(service_json[0]['Spec']['Mode']['Replicated']['Replicas'])
    return current_replicas

# HK: The function gets the number of replicas for a given specific node at that point
# Param: base name of that vm (eg. iot-edge from the name: iot-edge.20170725)
# Returns: the number of replicas for the given node
def get_macro_replicas(base_name):
    counter = 0
    result = run_command("sudo docker node ls")

    arr = result.split("\n")
    for i in range(0, len(arr)):
        if arr[i].__contains__(base_name):
            counter += 1
    return counter

"""
RR: This was the old method of running commands (using paramiko client to ssh into the same machine).
    This adds a lot of complexity and overhead to develop/deploy the autoscaler. Hence removing it.
# This function basically gets a ssh connection to the swarm master
# It gets the required information from the config file
def get_client(config_file, pkey_password_file, pkey_file):

    config = read_config_file(config_file)
    f = open(pkey_password_file, 'r')
    pkey_password = f.read().replace('\n', '')

    host = config.get('swarm', 'master_ip')
    user_name = config.get('swarm', 'user_name')

    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(host, username=user_name, password=pkey_password, key_filename=pkey_file)
    except paramiko.SSHException as e:
        print(str(e))

    return client

# This function basically executes the command on the ssh connection
def run_command(command):

    config_file = eng.CONFIG_NAME
    pkey_password_file = eng.PKEY_PASSWORD
    pkey_file = eng.PKEY_FILE

    client = get_client(config_file, pkey_password_file, pkey_file)
    stdin, stdout, stderr = client.exec_command(command, timeout=120)
    exit_status = stdout.channel.recv_exit_status()

    if exit_status == 0:
        result = ""
        # If you are provisioning VM, you want to see the output of command
        if "provision_vm" in command:
            for line in stdout:
                print('... ' + line.strip('\n'))
                result = result + line
        else:
            result = stdout.read()

    client.close()
    return result
"""
