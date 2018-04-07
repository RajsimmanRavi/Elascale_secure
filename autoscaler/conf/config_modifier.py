from autoscaler import util
import os
import configparser

def get_names(services, serv_option):

    return_list = []
    services_list = services.split("\n")
    for serv in services_list:
        if serv:
            return_list.append(serv.replace("'",""))
    return return_list

def read_write_config(f_name, mode_option, config):

    with open(f_name, mode_option) as f:
        if mode_option == "r":
            config.readfp(f)
        else:
            config.write(f)

    return config

def empty_file(f_name):

    config = configparser.ConfigParser()
    config = read_write_config(f_name, "r", config)

    # Empty the old file
    for sect in config.sections():
        config.remove_section(sect)

    config = read_write_config(f_name, "w", config)

def add_config_sections(f_name, add_list, ignore_list, serv_option):
    ignore_list = ignore_list.split(",")
    config = configparser.ConfigParser()
    for curr in add_list:
        # If microservice not part of ignore_list, then add it to config file
        if not (any(substring in curr for substring in ignore_list)):
            config.add_section(curr)
            config.set(curr, 'cpu_up_lim', '0.6')
            config.set(curr, 'memory_up_lim', '1.0')
            config.set(curr, 'cpu_down_lim', '0.4')
            config.set(curr, 'memory_down_lim', '0.2')
            config.set(curr, 'up_step', '1')
            config.set(curr, 'down_step', '-1')
            config.set(curr, 'max_replica', '4')
            config.set(curr, 'min_replica', '1')

            if serv_option == "macro":
                config.set(curr, "max_no_container", '4')

    new_config = read_write_config(f_name, "w", config)

def change_config(micro_f_name, macro_f_name, ignore_micro_list, ignore_macro_list):

    #First, empty the files
    empty_file(micro_f_name)
    empty_file(macro_f_name)

    config = configparser.ConfigParser()

    microservices = util.run_command("sudo docker service ls --format '{{.Name}}'")
    curr_services = get_names(microservices, "micro")
    add_config_sections(micro_f_name, curr_services, ignore_micro_list, "micro")

    macroservices = util.run_command("sudo docker node ls --format '{{.Hostname}}'")
    curr_nodes = get_names(macroservices, "macro")

    add_config_sections(macro_f_name, curr_nodes, ignore_macro_list, "macro")
