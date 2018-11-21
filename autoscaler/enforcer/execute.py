import json
import time
import os
import configparser
from datetime import datetime
#import gevent
from autoscaler.conf import engine_config as eng
from autoscaler import util
import pandas as pd

def scale_microservice(service_name, value):

    # Read the current config files
    micro_config = util.read_config_file(eng.MICRO_CONFIG)

    if micro_config[service_name]['auto_scale']:

        print("### Scaling micro_service: "+service_name+" of value: "+str(value))

        current_replica = util.get_micro_replicas(service_name)
        max_replica = int(micro_config.get(service_name, 'max_replica'))
        min_replica = int(micro_config.get(service_name, 'min_replica'))

        # This represents the total number of services 'after' it has been scaled
        total_replica = int(current_replica)+int(value)

        if total_replica > max_replica:
            print('### Abort micro scaling for microservice: '+service_name+' due to max replica limit: '+str(max_replica)+'.\n')
            return

        elif total_replica < min_replica:
            print('### Abort micro scaling for microservice: '+service_name+' due to min replica limit: '+str(min_replica)+'.\n')
            return

        else:
            """
            # You need to check whether the total_replicas exceeds max_no_container (in MACRO_CONFIG)
            macro_config = util.read_config_file(eng.MACRO_CONFIG)

            macro_service = util.get_macroservice(service_name)
            max_no_containers = int(micro_config.get(macro_service, 'max_no_container'))

            if total_replicas > max_no_containers:

                print("----- Maximum Number of Replicas exceeded for Macroservice.... Hence, autoscaling Macroservice: " + macroservice + " first\n")
                print("----- Scaling microservice: " + service_name + " to: " + str(total_replica) +" at time: " + str(st) + "\n")
            """

            st = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            print("----- Scaling microservice: " + service_name + " to: " + str(total_replica) +" at time: " + str(st) + "\n")

            result = util.run_command("sudo docker service scale "+service_name+"="+str(total_replica))
            return
    else:
        print("### 'auto_scale' set to False. Abort Scaling for microservice: "+service_name+"!")


def scale_macroservice(host_name, value):

    # Read the current config file
    macro_config = util.read_config_file(eng.MACRO_CONFIG)

    if macro_config[host_name]['auto_scale']:

        print("### Scaling macro_service: "+host_name+" of value: "+str(value))

        base_name = host_name.split('.')[0]

        current_replica = util.get_macro_replicas(base_name)

        max_replica = int(macro_config.get(base_name, 'max_replica'))
        min_replica = int(macro_config.get(base_name, 'min_replica'))

        # This represents the total number of services 'after' it has been scaled
        # 'value' variable tells whether to scale down ( - value) or scale up ( + value)
        total_replica = int(current_replica)+int(value)

        if total_replica > max_replica:
            print('### Abort macro scaling for '+host_name+' due to max replica limit: '+str(max_replica)+'.\n')
            return

        if total_replica < min_replica:
            print('### Abort macro scaling for '+host_name+' due to min replica limit: '+str(min_replica)+'.\n')
            return

        else:
            st = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            if value > 0:
                print("====> Scaling out the macroservice: "+host_name+" by "+str(value)+" at time: " + str(st) +"\n")
                new_vm_name = util.add_vm(host_name)  # add
            else:
                #value < 0
                print("====> Scaling in the macroservice: "+host_name+" by -"+str(value)+" at time: " + str(st) +"\n")
                util.remove_vm(host_name)  # remove
    else:
        print("### 'auto_scale' set to False. Abort Scaling for macroservice: "+host_name+"!")

