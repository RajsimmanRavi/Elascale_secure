import json
import time
import os
import configparser
from datetime import datetime
#import gevent
from autoscaler.conf import engine_config as eng
from autoscaler import util

def scale_microservice(service_name, value):

    # Read the current config file
    micro_config = util.read_config_file(eng.MICRO_CONFIG)

    print("### Scaling micro_service: "+service_name+" of value: "+str(value))

    current_replica = util.get_micro_replicas(service_name)
    max_replica = int(micro_config.get(service_name, 'max_replica'))
    min_replica = int(micro_config.get(service_name, 'min_replica'))

    # This represents the total number of services 'after' it has been scaled
    total_replica = int(current_replica)+value

    if total_replica > max_replica:
        print('### Abort micro scaling for microservice: '+service_name+' due to max replica limit: '+str(max_replica)+'.\n')
        return

    elif total_replica < min_replica:
        print('### Abort micro scaling for microservice: '+service_name+' due to min replica limit: '+str(min_replica)+'.\n')
        return

    else:
        st = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        print("----- Scaling microservice: " + service_name + " to: " + str(total_replica) +" at time: " + str(st) + "\n")
        #gevent.sleep(0)
        result = util.run_command("sudo docker service scale "+service_name+"="+str(total_replica))
        return

def scale_macroservice(host_name, value):

    # Read the current config file
    macro_config = util.read_config_file(eng.MACRO_CONFIG)

    print("### Scaling macro_service: "+host_name+" of value: "+str(value))

    base_name = host_name.split('.')[0]

    current_replica = util.get_macro_replicas(base_name)

    max_replica = int(macro_config.get(base_name, 'max_replica'))
    min_replica = int(macro_config.get(base_name, 'min_replica'))

    # This represents the total number of services 'after' it has been scaled
    # 'value' variable tells whether to scale down ( - value) or scale up ( + value)
    total_replica = current_replica+value

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
            new_vm_name = add_vm(host_name)  # add
        else:
            #value < 0
            print("====> Scaling in the macroservice: "+host_name+" by -"+str(value)+" at time: " + str(st) +"\n")
            remove_vm(host_name)  # remove
