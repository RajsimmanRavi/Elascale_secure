import os
import configparser
from autoscaler import util
import autoscaler.conf.engine_config as eng

def get_names(services):
    return_list = []
    services_list = services.split("\n")
    for serv in services_list:
        if serv:
            return_list.append(serv.replace("'",""))
    return return_list

def remove_config_sections(f_name, remove_list):
    #print("Remove list: %s" %(str(remove_list)))
    config = util.read_config_file(f_name)

    for sect in config.sections():
        if sect in remove_list:
            config.remove_section(sect)

    config = util.write_config_file(f_name, "w", config)

def add_config_sections(f_name, add_list):
    #print("Add list: %s" %(str(add_list)))
    config = configparser.ConfigParser()
    for curr in add_list:
        config.add_section(curr)
        config.set(curr, 'cpu_up_lim', '0.6')
        config.set(curr, 'mem_up_lim', '1.0')
        config.set(curr, 'cpu_down_lim', '0.4')
        config.set(curr, 'mem_down_lim', '0.2')
        config.set(curr, 'up_step', '1')
        config.set(curr, 'down_step', '-1')
        config.set(curr, 'max_replica', '4')
        config.set(curr, 'min_replica', '1')

        if f_name == eng.MACRO_CONFIG:
            config.set(curr, "max_no_container", '4')

    new_config = util.write_config_file(f_name, "a", config)

def filter_list(services, ignore_list):
    final_list = []
    for serv in services:
        if not (any(substring in serv for substring in ignore_list)):
            final_list.append(serv)
    return final_list

def update_services(ignore_list, f_name):
    # Make it into a list
    ignore_list = ignore_list.split(',')

    file_services = util.read_config_file(f_name).sections()

    if f_name == eng.MICRO_CONFIG:
        services = util.run_command("sudo docker service ls --format '{{.Name}}'")
    else:
        services = util.run_command("sudo docker node ls --format '{{.Hostname}}'")

    running_services = get_names(services)
    running_services = filter_list(running_services, ignore_list)

    #print("file_services: %s" % str(file_services))
    #print("running_services: %s" % str(running_services))

    if len(file_services) != len(running_services):
        # If more services are listed in file than it is actually running, then some services must have exited
        if len(file_services) > len(running_services):
            exited_services = list(set(file_services) - set(running_services))
            # Remove these services from file
            remove_config_sections(f_name, exited_services)
        else:
            # Else, new services are added, hence add them to file
            new_services = list(set(running_services) - set(file_services))
            # Add these services to file
            add_config_sections(f_name, new_services)

def update_config():

    update_services(eng.IGNORE_MICRO, eng.MICRO_CONFIG)
    update_services(eng.IGNORE_MACRO, eng.MACRO_CONFIG)
