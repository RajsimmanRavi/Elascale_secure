import configparser
from elasticsearch import Elasticsearch
from prettytable import PrettyTable
import monitor
import plan
import execute
import util
import change_micro_macro_config
import engine_config

#from parse_dockbeat import *

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

def pretty_print_util(service_type, data):
    """ Pretty prints Utilization of Micro/macroservice on terminal/docker logs

    Args:
        service_type: 'Micro' or 'Macro' keyword for printing on column header
        data: Dictionary of utilization data (get more info on get_util_info() function)
    """
    service = data["service"]
    curr_cpu = data["curr_cpu_util"]
    curr_mem = data["curr_mem_util"]
    high_cpu = data["high_cpu_threshold"]
    low_cpu = data["low_cpu_threshold"]
    high_mem = data["high_mem_threshold"]
    low_mem = data["low_mem_threshold"]

    x = PrettyTable()
    x.field_names = [service_type+"service", low_cpu+" < CPU < "+high_cpu, low_mem+" < Memory < "+high_mem]
    x.add_row([service, curr_cpu, curr_mem])

    print(x)

    x.clear_rows()
    x.clear()

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
    result["high_cpu_threshold"] = config.get(service, 'cpu_up_lim') # Ex second argument should be: cpu_up_lim
    result["low_cpu_threshold"] = config.get(service, 'cpu_down_lim') # Ex second argument should be: cpu_low_lim
    result["high_mem_threshold"] = config.get(service, 'memory_up_lim') # Ex second argument should be: cpu_up_lim
    result["low_mem_threshold"] = config.get(service, 'memory_down_lim') # Ex second argument should be: cpu_low_lim

    return result


def check_status(service_type, service, curr_util, config):
    """ Fetches status for a specific microservice/macroservice

    Args:
        service_type: Keyword 'Micro' or 'Macro' to differentiate type of service
        service: name of service
        curr_util: utilization data of all micro/macroservices
        config: configuration of micro/macroservices

    Returns:
        Dictionary of data:
            result = {
                "service": name of the macroservice
                "status": Keyword 'High', 'Normal' or 'Low' mentioning the status
            }
    """
    if service_type == "Macro":
        # First get the macroservice runnning the service
        service = util.get_macroservice(service)

    data = get_util_info(service, curr_util, config)
    pretty_print_util(service_type, data)

    # Then check whether the macroservice can handle the load to spin another microservice
    status = check_threshold(service, data["high_cpu_threshold"], data["low_cpu_threshold"], data["curr_cpu_util"])

    result = {}
    result["service"] = service
    result["status"] = status

    return result

def discrete_policy(micro_status, macro_status, micro, macro, micro_config, macro_config):
    """ Performs discrete policy for autoscaling engine.

    Algorithm:
        if microservice crosses high threshold:
            if macroservice crosses high threshold:
               scale-up macroservice
            scale-up microservice
        else:
            scale-down microservice

            if macroservice crosses low threshold:
                scale-down macroservice

     Args:
         micro_status: Keyword 'High', 'Normal', or 'Low' mentioning the status of microservice
         macro_status: Keyword 'High', 'Normal', or 'Low' mentioning the status of macroservice
         micro: name of the microservice
         macro: name of the macroservice
         micro_config: configuration of microservice
         macro_config: configuration of macroservice
    """

    if micro_status == "High":
        if macro_status == "High":
            execute.scale_macroservice(macro, int(macro_config.get(macro, 'up_step')))

        # Finally, scale up the microservice
        execute.scale_microservice(micro, int(micro_config.get(micro, 'up_step')))
    else:
        # Which means it's low low_cpu
        # Scale down the microservice first, just to be on the safe side
        execute.scale_microservice(micro, int(micro_config.get(micro, 'down_step')))

        # Then check whether the macroservice's cpu_util is too low (so we can remove one)
        if macro_status == "Low":
            execute.scale_macroservice(macro, int(macro_config.get(macro, 'down_step')))

def compare_util(micro_config, micro_utilization, macro_config, macro_utilization):
    """ Compares utilization of micro/macroservices and calls discrete autoscaling policy.
        TODO: Currently uses only CPU, need to do for Memory and Network.
        TODO: Use Adaptive policies.

    Args:
        micro_config: configuration of microservices
        micro_utilization: utilization data of microservices
        macro_config: configuration of macroservices
        macro_utilization: utilization data of macroservices
    """

    services = micro_config.sections()
    for micro in services:

        micro_status = check_macro_status("Micro", micro, micro_utilization, micro_config)

        if micro_status["status"] == "Normal":
            print("Within CPU limit. Nothing to do for service: "+micro+"!\n")
        else:
            macro_status = check_macro_status("Macro", micro, macro_utilization, macro_config)
            discrete_policy(micro_status["status"], macro_status["status"], micro, macro_status["service"], micro_config, macro_config)

def main():
    """ Function to initialize variables, monitor micro/macroservices every interval and calls compare_util function.
    """

    # Getting all the constants from engine_config file
    config_name = engine_config.CONFIG_NAME
    micro_config_file = engine_config.MICRO_CONFIG
    macro_config_file = engine_config.MACRO_CONFIG
    ignore_micro = engine_config.IGNORE_MICRO
    ignore_macro = engine_config.IGNORE_MACRO
    monitoring_interval = engine_config.MONITORING_INTERVAL

    # Read config file
    config = util.read_config_file(config_name)
    ca_cert = str(config.get('elasticsearch', 'ca_cert'))

    # Get Elasticsearch client
    # For this to work, you need to add 'elasticsearch' to /etc/hosts
    es = Elasticsearch([{'host': 'elasticsearch', 'port': int(config.get('elasticsearch', 'port'))}], use_ssl=True, ca_certs=ca_cert)

    while True:

        # Update the config files first!
        change_micro_macro_config.change_config(micro_config_file,macro_config_file, ignore_micro, ignore_macro)

        micro_config = util.read_config_file(micro_config_file)
        macro_config = util.read_config_file(macro_config_file)

        micro_util = monitor.get_microservices_utilization(es)
        macro_util = monitor.get_macroservices_utilization(es)

        compare_util(micro_config, micro_util, macro_config, macro_util)

        print("****** Completed monitoring! Wait for "+str(monitoring_interval)+" seconds. *****")

        util.progress_bar(monitoring_interval)

if __name__ == "__main__":

    main()
