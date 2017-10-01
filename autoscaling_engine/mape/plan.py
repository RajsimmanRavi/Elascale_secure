import util
import json
import re

"""
RR: This file contains a number of helper functions that helps Elascale execute specific actions to the system (eg. scale service). Hence, I named this file 'plan'!
Functions written by Hamzeh Khazaei (which is mostly) are noted on the comments by HK
Functions written by me (which is one, as of now) are noted on the comments by RR
"""

# HK: Function that inspects the microservice
# Param: service name
# Returns: the output of the command: sudo docker service inspect $service_name
def inspect_service(service_name):
    result = util.run_command("sudo docker service inspect "+service_name)
    return str(result.output)

# HK: Function that inspects the macroservice
# Param: vm name
# Returns: the output of the command: sudo docker-machine inspect $vm_name
def inspect_machine(vm_name):
    result = util.run_command("sudo docker-machine inspect "+vm_name)
    return str(result.output)

# HK: Function that inspects the node
# Param: vm name
# Returns: the output of the command: sudo docker node inspect $vm_name
def inspect_swarm_node(vm_name):
    result = util.run_command("sudo docker node inspect "+vm_name)
    return str(result.output)



# HK: Function that finds the latest added machine for that macroservice
# Param: base name of the macroservice (eg. iot-edge from the name: iot-edge.20170725)
# Returns: the entire name of the latest added node (i.e. iot-edge.20170725)
def find_candidate_instance_to_remove(base_name):

    vm_names = []
    result = util.run_command("sudo docker node ls")
    words = str(result.output).replace("\\", " ").replace("\n", " ").split(" ")

    for word in words:
        if word.__contains__(base_name):
            vm_names.append(word)
    if vm_names.__len__() > 0:
        vm_names.sort(reverse=True)
        return vm_names[0]  # return the instance that had been added lately.
    else:
        return ''

# HK: Extract the original node name; the base name is always before '.'
# We use base name as the name for finding VMs in the same family.
# All VMs with the same prefix, i.e., before dot, are in the same group.
# Param: entire name of the macroservice (eg. iot-edge.20170725)
# Returns: the base name of that macroservice (eg. iot-edge)
def get_macro_base_name(name):
    return name.split('.')[0]

# HK: Get the labels given a specific node
# Param: node name
# Returns: label(s) of that name (eg. loc=edge)
def get_labels(node_name):
    node_info = inspect_swarm_node(node_name)
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
    command = "sudo docker service ps "+microservice
    result = util.run_command(command)

    # The result will contain the line that has the node name
    label_line = re.search('iot-(.*)', result.output).group(1)

    # split the line to get only the node name
    macroservice = "iot-"+label_line.split(" ")[0]

    print("Macroservice: "+macroservice+"\n")

    return macroservice

# RR: This function fetches the error status (if any) of the macroservice
# This is mainly used when creating a vm (or macroservice)
def check_macroservice_status(vm_name):
    result = util.run_command("sudo docker-machine ls")

    # split by newline
    vms = str(result.output).split("\n")

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
    result = util.run_command("sudo docker swarm join-token worker")
    words = str(result.output).replace("\\", " ").replace("\n", " ").split(" ")
    token_index = words.index("--token") + 1

    token = words[token_index]
    master_ip_port = words[-3]
    return token, master_ip_port

# HK: This function gets the number of replicas for a given specific service at that point
# Param: service name
# Returns: the number of replicas for the given specific service
def get_micro_replicas(service_name):
    service_info = inspect_service(service_name)
    service_json = json.loads(service_info, encoding='utf8')
    current_replicas = int(service_json[0]['Spec']['Mode']['Replicated']['Replicas'])
    return current_replicas

# HK: The function gets the number of replicas for a given specific node at that point
# Param: base name of that vm (eg. iot-edge from the name: iot-edge.20170725)
# Returns: the number of replicas for the given node
def get_macro_replicas(base_name):
    counter = 0
    result = util.run_command("sudo docker node ls")

    arr = str(result.output).split("\n")
    for i in range(0, len(arr)):
        if arr[i].__contains__(base_name):
            counter += 1
    return counter
