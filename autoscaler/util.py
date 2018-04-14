import os
import sys
import json
import subprocess as sp
import time
from datetime import datetime
from tqdm import tqdm
from prettytable import PrettyTable
import configparser
import autoscaler.conf.engine_config as eng
#import paramiko # not needed anymore

def get_vm_info(vm):
    """ Function to fetch vm information. Used for creating another vm with same specs.
    Args: vm name
    Returns: vm info dict
    """
    inspect_vm = run_command("sudo docker-machine inspect "+vm)
    vm_json = json.loads(inspect_vm, encoding='utf8')

    vm_info = {}

    vm_info["username"] = vm_json['Driver']['Username']
    vm_info["password"] = vm_json['Driver']['Password']
    vm_info["auth_url"] = vm_json['Driver']['AuthUrl']
    vm_info["region"] = vm_json['Driver']['Region']
    vm_info["tenant"] = vm_json['Driver']['TenantName']
    vm_info["flavor"] = vm_json['Driver']['FlavorName']
    vm_info["image"] = vm_json['Driver']['ImageName']
    vm_info["network_name"] = vm_json['Driver']['NetworkName']
    vm_info["network_id"] = vm_json['Driver']['NetworkId']

    return vm_info

def get_util_info(service, curr_util, config):
    """ Fetches the current utilization  along with high and low thresholds defined in config file.
    Args:
        service: name of the service
        curr_util: the current utilization data of all services
        config: config file
    Returns: dictionary of result data
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

def get_label(node_name):
    """ Function that returns the label of a specific docker node (eg. label can be loc=edge).
        Args: node_name: name of the docker node
        Returns: dictionary of the label: dict["label"] = "value"
    """
    return_dict = {}
    cmd = "sudo docker node inspect -f '{{ range $k, $v := .Spec.Labels }}{{ $k }}={{ $v }} {{end}}' "+node_name
    labels = run_command(cmd)
    return_dict[labels.split("=")[0]] = labels.split("=")[1]
    return return_dict

def get_macroservice(micro):
    cmd = "sudo docker service ps "+micro+" --format '{{ .Node }}'"
    result = run_command(cmd)
    # Get only one, if more returned
    macro = result.split("\n")[0]
    return macro

def get_micro_replicas(micro):
    cmd = "sudo docker service inspect "+micro+" -f '{{ .Spec.Mode.Replicated.Replicas }}'"
    curr_replicas = run_command(cmd)
    return curr_replicas

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

def get_latest_vm(vm_name):
    """ Function to get the latest added vm, given the base name.
        As more macroservices are created (to manage workload), the added vms' names contain a prefix and suffix separated by '.'
        For example, if more macroservices are needed for iot-edge, then the names would be iot-edge.xx
        So, given the base_name: iot-edge, we find the last added vm (based on their created timestamps)

        Args: vm_name: base vm name of the macroservice (Eg. 'iot-xxxx' of 'iot-xxxx.xx' )
        Returns: vm name that was last added
    """
    cmd = "sudo docker node ls -f 'name="+vm_name+"' --format '{{.Hostname}}'"
    result = run_command(cmd)
    curr_vms = result.split('\n')

    # Run this loop iteratively, so that you can store the first vm's created timestamp as latest_time.
    # You need this to compare with other vm's timestamps and find the latest vm created
    for i in range(len(curr_vms)):
        # Remove +0000 UTC bs from the string to properly match with string format
        cmd = "sudo docker node inspect -f '{{ .CreatedAt }}' "+curr_vms[i]
        created_at = run_command(cmd)[:-13]
        created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')

        if i == 0:
            latest_time = created_datetime
            latest_vm = curr_vms[i]
        else:
            # If created time of this VM is later than latest_time, then this is the last vm added.
            if created_datetime > latest_time:
                latest_time = created_datetime
                latest_vm = curr_vms[i]

    return latest_vm

"""
def run_command(command):
    p = sp.Popen(command, shell=True, stdout=sp.PIPE)
    output, err = p.communicate()

    output = str(output.strip(), 'utf-8')
    return output
"""

def run_command(command):
    try:
        process = sp.Popen(command, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
        output, err = process.communicate(timeout=180)
    except Exception as e:
        print("Caught error while running command...Exiting!")
        print(str(e))
        sys.exit(1)

    if process.returncode != 0:
        raise sp.CalledProcessError(process.returncode, command)
        sys.exit(1)
    else:
        output = str(output.strip(), 'utf-8')

    return output

def add_vm(vm_name):
    # get info of the vm
    vm_info = get_vm_info(vm_name)
    new_vm_name = vm_name + "." + time.strftime("%Y%m%d%H%M%S", time.localtime())

    print(new_vm_name + ' VM is being provisioned on the cloud ...')

    # Get the label from the base vm
    label_dict = get_label(vm_name)

    create_vm_cmd = "sudo docker-machine create --driver openstack \
        --openstack-auth-url "+vm_info['auth_url']+" \
        --openstack-insecure \
        --openstack-flavor-name "+vm_info['flavor']+" --openstack-image-name "+vm_info['image']+" \
        --openstack-tenant-name "+vm_info['tenant']+" --openstack-region "+vm_info['region']+" \
        --openstack-net-name "+vm_info['network_name']+" \
        --openstack-sec-groups savi-iot --openstack-ssh-user ubuntu \
        --openstack-username "+vm_info['username']+" --openstack-password "+vm_info['password']+" "+new_vm_name

    # These all have try/except blocks when executing commands, hence not adding extra try/excepts
    run_command(create_vm_cmd)
    add_swarm_node(new_vm_name)
    add_label(new_vm_name, label_dict)
    prepare_for_beats(new_vm_name)

    return new_vm_name

def remove_vm(vm_name):
    node_name = get_latest_vm(vm_name)
    print("\nRemoving the swarm node: " + node_name+"\n")
    remove_swarm_node(node_name)
    run_command("sudo docker-machine rm --force "+node_name)

def add_swarm_node(vm_name):
    cmd="sudo docker swarm join-token worker | grep -v 'add' | tr -d '/\' 2> /dev/null"
    result = run_command(cmd)

    join_cmd = "sudo "+result
    execute_on_vm_cmd = "sudo docker-machine ssh "+vm_name+" "+join_cmd
    result = run_command(execute_on_vm_cmd)

def remove_swarm_node(node_name):
    result = run_command("sudo docker-machine ssh "+node_name+ " sudo docker swarm leave")
    result = run_command("sudo docker node rm --force "+node_name)

def add_label(vm_name,label_dict):
    label = list(label_dict.keys())[0]
    value = list(label_dict.values())[0]

    cmd = "sudo docker node update --label-add "+label+"="+value+" "+vm_name
    run_command(cmd)

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

def prepare_for_beats(vm_name):

    print('\nPreparing VM for Beats: ' + vm_name)

    # Get where the config files are located. This can be found on engine.config file
    elascale_config_dir = eng.PLATFORM_CONFIG_DIR

    # Get where the Elascale root directory are located. This can be found on engine.config file
    elascale_certs_dir = eng.PLATFORM_CERTS_DIR

    # Copy the metricbeat.yml on swarm-master to the new node
    run_command("sudo docker-machine scp "+elascale_config_dir+"/metricbeat.yml "+vm_name+":~")

    # Change the hostname on the new metricbeat.yml
    sed_command = 'sed -i "s/name: ".*"/name: \\"'+vm_name+'\\"/g" ~/metricbeat.yml'
    run_command("sudo docker-machine ssh "+vm_name+" '"+sed_command+"'")

    # Copy the dockbeat.yml on swarm-master to the new node
    run_command("sudo docker-machine scp "+elascale_config_dir+"/dockbeat.yml "+vm_name+":~")

    # Create certs directory in home directory to store the elasticsearch_certificate.pem
    run_command("sudo docker-machine ssh "+vm_name+" mkdir ~/certs")

    # Copy elasticsearch_certificate.yml to the new machine
    run_command("sudo docker-machine scp "+elascale_certs_dir+"/elasticsearch_certificate.pem "+vm_name+":~/certs/")

    # Create /volumes/dockbeat-logs dir on the new node (required for dockbeat to work properly)
    run_command("sudo docker-machine ssh "+vm_name+" sudo mkdir -p /volumes/dockbeat-logs/")

    print('dockbeat and metricbeat yml files have been copied/configured successfully.')