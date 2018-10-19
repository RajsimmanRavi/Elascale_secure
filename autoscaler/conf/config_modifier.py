import os
import configparser
from autoscaler import util
import autoscaler.conf.engine_config as eng

def get_names(services):
    return_list = []
    services_list = services.split('\n')
    for serv in services_list:
        if serv:
            return_list.append(serv.replace("'",""))
    return return_list

def remove_config_section(f_name, remove_service):
    #print("Remove list: %s" %(str(remove_list)))
    config = util.read_config_file(f_name)

    if remove_service in config.sections():
        config.remove_section(remove_service)

    config = util.write_config_file(f_name, "w", config)

def update_config_attribute(service_type, section, attribute, value):
    if service_type == "Micro":
        config = util.read_config_file(eng.MICRO_CONFIG)
        f_name = eng.MICRO_CONFIG
    else:
        config = util.read_config_file(eng.MACRO_CONFIG)
        f_name = eng.MACRO_CONFIG

    config.set(section, attribute, value)
    util.write_config_file(f_name, "w", config)

    #print(config[section][attribute])

def add_config_section(f_name, new_section):
    #print("Add list: %s" %(str(add_list)))
    config = configparser.ConfigParser()
    config.add_section(new_section)
    config.set(new_section, 'cpu_up_lim', '0.65')
    config.set(new_section, 'mem_up_lim', '1.0')
    config.set(new_section, 'cpu_down_lim', '0.2')
    config.set(new_section, 'mem_down_lim', '0.2')
    config.set(new_section, 'up_step', '1')
    config.set(new_section, 'down_step', '-1')
    config.set(new_section, 'max_replica', '4')
    config.set(new_section, 'min_replica', '1')
    config.set(new_section, 'auto_scale', 'True')

    if f_name == eng.MACRO_CONFIG:
        config.set(new_section, "max_no_container", '2')

    new_config = util.write_config_file(f_name, "a", config)


def update_services(ignore_list, f_name, apps=None):
    #print(ignore_list)
    # Make it into a list
    ignore_list = ignore_list.split(',')

    file_services = util.read_config_file(f_name).sections()

    if f_name == eng.MICRO_CONFIG:
        services = []
        for app in apps:
            curr_services = util.run_command("sudo docker stack services "+app+" --format '{{.Name}}'")
            curr_services = get_names(curr_services)
            services += curr_services

    else:
        services = util.run_command("sudo docker node ls --format '{{.Hostname}}'")
        services = get_names(services)

    running_services = services
    # This was the old way of filtering it out. We just ignore them completely.
    # This does not work well with anomaly detection mechanisms
    # We want to add a section 'auto_scale = True/False' on config
    # Set it as True if the service is not in IGNORE_MICRO (engine_config.py)

    #running_services = util.filter_list(services, ignore_list)

    #print("file_services: %s" % str(file_services))
    #print("running_services: %s" % str(running_services))

    # Add new sections if needed
    for service in running_services:
        if service not in file_services:
            add_config_section(f_name, service)

    # Remove old sections if needed
    for service in file_services:
        if service not in running_services:
            remove_config_section(f_name, service)

    # Update auto_scale label
    for serv in file_services:
        if (any(substring in serv for substring in ignore_list)):
            if f_name == eng.MICRO_CONFIG:
                update_config_attribute("Micro", serv, "auto_scale", 'False')
            else:
                update_config_attribute("Macro", serv, "auto_scale", 'False')
        else:
            if f_name == eng.MICRO_CONFIG:
                update_config_attribute("Micro", serv, "auto_scale", 'True')
            else:
                update_config_attribute("Macro", serv, "auto_scale", 'True')

def update_config():
    apps = util.get_app_stacks()
    update_services(eng.IGNORE_MICRO, eng.MICRO_CONFIG, apps)
    update_services(eng.IGNORE_MACRO, eng.MACRO_CONFIG)

if __name__=="__main__":
    update_config()
