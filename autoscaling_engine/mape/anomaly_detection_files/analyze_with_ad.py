import os
import sys
import time
import datetime
import configparser
import monitor
import plan
import execute
import util
from change_micro_macro_config import change_config
#from parse_dockbeat import *

"""
Default Global variables initialized here
"""
monitoring_interval = 60  # in seconds;

config_path = os.path.realpath('./../config')
micro_config_file_name = config_path + "/microservices.ini"
macro_config_file_name = config_path + "/macroservices.ini"

def check_high_cpu(service, config, utilization):

    if utilization[service]['cpu'] > float(config.get(service, 'cpu_up_lim')):
        return True
    else:
        return False

def check_low_cpu(service, config, utilization):

    if utilization[service]['cpu'] < float(config.get(service, 'cpu_down_lim')):
        return True
    else:
        return False

def print_cpu_util(serv, serv_utilization, serv_config):

    print("\n-------------- MONITOR SERVICE: "+serv+" --------------")
    print("CPU utilization: "+str(round(serv_utilization[serv]['cpu'], 2)))
    print("CPU_UP_LIM config: "+str(serv_config.get(serv, 'cpu_up_lim')))
    print("CPU_DOWN_LIM config: "+str(serv_config.get(serv, 'cpu_down_lim')))

def compare_cpu_util(micro_config, micro_utilization, macro_config, macro_utilization):

    services = micro_config.sections()
    for micro in services:
        if util.str_to_bool(micro_config.get(micro, 'auto_scale')):

            print_cpu_util(micro, micro_utilization, micro_config)

            high_cpu = check_high_cpu(micro, micro_config, micro_utilization)
            low_cpu = check_low_cpu(micro, micro_config, micro_utilization)

            if (not high_cpu) and (not low_cpu):

                print("Within CPU limit. Nothing to do for service: "+micro+"!\n")

            elif high_cpu:

                # First get the macroservice runnning the service
                macro = plan.get_macroservice(micro)

                # Print the cpu info
                print_cpu_util(macro, macro_utilization, macro_config)

                start = datetime.now()
                result = parse_dockbeat(micro)
                stop = datetime.now()
                print("It took %s seconds to process dockbeat data!" %(str((stop-start).seconds)))
                #result = False
                if result == False:
                    # Check if Macro Autoscaling is set to True
                    if util.str_to_bool(macro_config.get(macro, 'auto_scale')):
                        # Then check whether the macroservice can handle the load to spin another microservice
                        if check_high_cpu(macro, macro_config, macro_utilization):
                            execute.scale_macroservice(macro, int(macro_config.get(macro, 'up_step')))
                    else:
                        print("Autoscaling for this macro: "+str(macro)+" is not set. Hence skipping...")

                    #Print time
                    st = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                    print("AUTOSCALING AT THIS TIME: "+st)
                    # Finally, scale up the microservice
                    execute.scale_microservice(micro, int(micro_config.get(micro, 'up_step')))

                else:
                    print("Anomaly Detected! Skip Autoscaling!!")
            else:
                # Which means it's low low_cpu
                print("LOW CPU UTIL!")
                # First get the macroservice runnning the service
                macro = plan.get_macroservice(micro)

                # Print the cpu info
                print_cpu_util(macro, macro_utilization, macro_config)

                #After finalized anomaly detection mechanism
                #result = parse_dockbeat(micro)
                result = False

                if result == False:

                    #Print time
                    st = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                    print("DOWNSCALING AT THIS TIME: "+st)

                    # Scale down the microservice first, just to be on the safe side
                    execute.scale_microservice(micro, int(micro_config.get(micro, 'down_step')))

                    # Check if Macro Autoscaling is set to True
                    if util.str_to_bool(macro_config.get(macro, 'auto_scale')):

                        # Then check whether the macroservice's cpu_util is too low (so we can remove one)
                        if check_low_cpu(macro, macro_config, macro_utilization):
                            execute.scale_macroservice(macro, int(macro_config.get(macro, 'down_step')))
                    else:
                        print("Autoscaling for this macro: "+str(macro)+" is not set. Hence skipping...")
                else:
                    print("Anomaly Detected! Skip Autoscaling!!")

            print("\n-------------- EVALUATION COMPLETED FOR MICROSERVICE: "+micro+" --------------\n")

def main():

    while True:
        # Update the config files first!
        change_config(micro_config_file_name,macro_config_file_name)

        micro_config = util.read_config_file(micro_config_file_name)
        macro_config = util.read_config_file(macro_config_file_name)

        micro_util = monitor.get_microservices_utilization()
        macro_util = monitor.get_macroservices_utilization()

        compare_cpu_util(micro_config, micro_util, macro_config, macro_util)

        print("****** Completed monitoring! Wait for "+str(monitoring_interval)+" seconds. *****")

        util.progress_bar(monitoring_interval)

if __name__ == "__main__":

    """ This is just for testing purposes locally. If finalized, you can remove these initializations """

    os.environ["PYTHONUFFERED"] = "0"
    os.environ["PKEY_PASSWORD"] = "/home/ubuntu/Elascale_secure/pass_key/pass_key_passphrase.txt"
    os.environ["PKEY_FILE"] = "/home/ubuntu/Elascale_secure/pass_key/pass_key"

    main()
