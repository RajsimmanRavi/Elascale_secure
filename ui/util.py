import ConfigParser
import docker
import os
import json
import requests
import sys

"""
    Function to read the Config ini file and return that variable.
"""
def read_file(f_name):
    Config = ConfigParser.ConfigParser()
    Config.read(f_name)

    return Config

"""
    Function to insert modified values to the appropriate config ini file (micro or macro).
    Returns nothing. If error occurs, the try/except on the called function will catch the error

    The argument is the received data from client/browser end. The format is in json:
    {"service_type": "xx", "service": "xx", "${config_param}": "xx" ...}

    service_type: defines whether it's a micro-service or macro-service
    service: define what service is getting modified (i.e. iot_app_cass, iot_edge_processor etc.)
    The other keys are basically the config_params (eg. cpu_up_lim, max_replica etc.)
    The corresponding values are the newly modified values that needs to be written to file.
"""
def write_file(data):
    Config = ConfigParser.ConfigParser()

    #Convert string to json
    data = json.loads(data)

    service_type = data["service_type"] # Tells us whether 'micro' or 'macro'
    service = data["service"]

    micro_file = os.environ['MICRO']
    macro_file = os.environ['MACRO']

    # Read appropriate ini file
    if service_type == "micro":
        Config.read(micro_file)
    else:
        Config.read(macro_file)

    #delete service_type and service keys from dict
    del data["service_type"]
    del data["service"]

    for key, value in data.iteritems():

        # Set appropriate values
        Config.set(service,key,value)

    #Write the changes to file

    if service_type == "micro":
        with open(micro_file, 'wb') as configfile:
            Config.write(configfile)
    else:
        with open(macro_file, 'wb') as configfile:
            Config.write(configfile)

"""
    Function to get the current macro-services (VMs) from the docker client.
    It creates a list and returns it
"""
def get_macro(client):

    nodes = client.nodes.list()
    macro_services = []

    for node, val in enumerate(nodes):
        #get label of the VM.
        #If label exists, then add it to the list. This way, we can remove IoT-app-controller VM
        label = nodes[node].attrs['Spec']['Labels']
        if label:
            macro_services.append(nodes[node].attrs['Description']['Hostname'])

    return macro_services

"""
    Function to get the current micro-services from the docker client.
    It creates a list and returns it
"""
def get_micro(client):

    services = client.services.list()
    micro_services = []

    for serv in services:
        serv_name = serv.attrs['Spec']['Name']

        micro_services.append(serv_name)

    return micro_services

"""
    Function to enter new services to the Microservices INI file.
    At the start of this web server, some services may be up and running, but not represented on the INI file.
    Hence, add them such that user can configure them as well
"""
def get_final_list(running_services, config_services, serv_type):

    config_serv_sections = config_services.sections() #ConfigParser sections are the services

    final_list = []

    for serv in running_services:
        if serv not in config_serv_sections:

            config = ConfigParser.ConfigParser()
            config.add_section(serv)
            config.set(serv, 'cpu_up_lim', 0.6)
            config.set(serv, 'mem_up_lim', 0.6)
            config.set(serv, 'cpu_down_lim', 0.4)
            config.set(serv, 'up_step', 1)
            config.set(serv, 'down_step', -1)
            config.set(serv, 'max_replica', 4)
            config.set(serv, 'min_replica', 1)
            config.set(serv, 'auto_scale', False)

            if serv_type == "macro":
                config.set(serv, 'max_no_container', 4)

                with open(os.environ['MACRO'], 'a') as configfile:
                    config.write(configfile)
            else:
                with open(os.environ['MICRO'], 'a') as configfile:
                    config.write(configfile)

        final_list.append(serv)

    return final_list

"""
    Function to insert dashboard ID inside the url link (used in the function down below)
    1st argument: dash_title: This is needed because we use different urls for different dshboards
    2nd argument: dash_id: The ID we need to insert into the url
    3rd argument: IP address of the elasticsearch
"""
def insert_id_url(dash_title, dash_id, elastic_ip_addr):
    # As per Byungchul, I need to look only the last 1 min for Host and Container statistics which has titles "HostStatics_1" and "ContainerStatistics_2". Therefore they have different links
    if ("_1" in dash_title) or ("_2" in dash_title):
        link = "https://"+elastic_ip_addr+":5601/app/kibana#/dashboard/"+dash_id+"?embed=true&_g=(refreshInterval%3A('%24%24hashKey'%3A'object%3A1659'%2Cdisplay%3A'5%20seconds'%2Cpause%3A!f%2Csection%3A1%2Cvalue%3A5000)%2Ctime%3A(from%3Anow-1m%2Cmode%3Arelative%2Cto%3Anow))"

    else:
        link = "https://"+elastic_ip_addr+":5601/app/kibana#/dashboard/"+dash_id+"?embed=true&_g=(refreshInterval%3A('%24%24hashKey'%3A'object%3A1659'%2Cdisplay%3A'5%20seconds'%2Cpause%3A!f%2Csection%3A1%2Cvalue%3A5000)%2Ctime%3A(from%3Anow-15m%2Cmode%3Aabsolute%2Cto%3Anow))"

    sys.stdout.flush()

    return link

"""
    Function to fetch the Kibana dashboard links. We decided to split one major dashboard into multiple smaller ones.
    1. Host Stats - focuses on VMs - Get last 1min stats
    2. Container Stats - Get last 1min stats
    3. All Graphs (Eg. CPU, mem etc.)
    4. All tables
"""
def get_kibana_links(elastic_ip_addr):
    elastic_ip_addr = "elasticsearch"
    req = requests.get("https://"+elastic_ip_addr+":9200/.kibana/dashboard/_search", verify=os.environ['NGINX_CERT'])
    output = req.json()

    output_dict = {}
    #get all the dashboard dictionaries
    dash_dicts = output["hits"]["hits"]

    #go through each dict and extract the dashboard IDs
    for dash in dash_dicts:

        #Our interested dashboards have titles with '_'. So filter only those ones
        if "_" in dash["_source"]["title"]:

            #get title of the dashboard
            dash_title = dash["_source"]["title"]

            #get id of the dashboard
            dash_id = dash["_id"]

            #append to output dict
            output_dict[dash_title] = insert_id_url(dash_title, dash_id, elastic_ip_addr)

    sys.stdout.flush()
    return output_dict

"""
   Checks whether user/pass is correct
"""

def check_password(username, password):

    if username == os.environ['USERNAME'] and password == os.environ['PASSWORD'] :
        return True
    else:
        return False
