from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
from autoscaler.policy.discrete import discrete_micro, discrete_macro
from autoscaler.policy.adaptive import adaptive_micro, adaptive_macro
import pandas as pd
import numpy as np
import sys
import argparse

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


parser = argparse.ArgumentParser(description="*** Autoscaler Arguments ***")
parser.add_argument('-ad', '--ad', help='Enable Anomaly Detection (True/False). Defaults to False', type=str2bool, nargs='?', default=False)
parser.add_argument('-p', '--policy', help='Discrete or Adaptive Policy Enable Anomaly Detection (d/a). Defaults to "d"', type=str, nargs='?', default='d')
args = parser.parse_args()

def start_process(ad):
    elascale = Elascale()
    elascale.set_elastic_client()
    elascale.set_config()

    # The first argument (Bool) mentions whether enable anomaly detection or not
    enable_ad = ad

    if enable_ad == True:
        print("Entering ad")
        from autoscaler.anomaly_detection import ad_util
        anomaly_scores = []
        detects = ad_util.init_detects(elascale)
        sample_counter = 0 # This is for how many times in investigation period

    while True:
        elascale.set_config()

        # Get apps currently runnning
        apps = util.get_app_stacks()
        for app in apps:

            services = util.get_stack_services(app)
            nodes = util.get_stack_nodes(app)

            print("app: %s nodes: %s" %(app,nodes))


            if enable_ad:
                final_score = ad_util.anomaly_detection(services, elascale.es, detects)
                current_replica = util.get_micro_replicas("iot_app_edge")

                if (final_score > (1 - 10e-5)):
                    print("Entered investigation period...")
                    sample_counter = 1
                    remove_extra_replicas(current_replica, "iot_app_edge")
                else:
                    if 0 < sample_counter <= eng.INVESTIGATION_PHASE_LENGTH:
                        print("Still in investigation period...")
                        remove_extra_replicas(current_replica, "iot_app_edge")
                        sample_counter += 1
                    else:
                        print("Exiting investigation period and start scaling procedure...")
                        sample_counter = 0
                        scale(services, elascale)
            else:
                # No anomaly detection enabled, go straight to scaling policy
                scale(services, nodes, elascale)

        util.progress_bar(eng.MONITORING_INTERVAL)

def scale(services, nodes, elascale):
    for micro in services:
        if micro == "iot_app_edge":
            if args.policy == 'd':
                discrete_micro(micro, elascale.es)
            else:
                adaptive_micro(micro, elascale.es)
    print("nodes: " %(nodes))
    for macro in nodes:
        if macro == "iot-edge":
            if args.policy == 'd':
                discrete_macro(macro, elascale.es)
            else:
                adaptive_macro(macro, elascale.es)
    """
    if micro == "iot_app_edge": # just scale stream processor, nothing else
        micro_status = util.check_status("Micro", micro, elascale.es)

        curr_info = util.get_cpu_util(micro,elascale.es, "Micro", "high")
        curr,thres = curr_info["util"], curr_info["thres"]

        if micro_status["status"] == "Normal":
            print("Within CPU limit. Nothing to do for service: "+micro+"!\n")
        else:
            #macro_status = util.check_status("Macro", micro, elascale.es)
            #discrete_alg(micro_status["status"], macro_status["status"], micro, macro_status["service"])
            #adaptive_alg(micro, macro_status["service"], elascale.es)
            adaptive_alg(micro,elascale.es) # For evaluating CNSM paper
    """

def remove_extra_resources(curr_replica, micro):
    if int(current_replica) != 1:
        print("replica not 1")
        result = util.run_command("sudo docker service scale "+micro+"="+str(1))

def main():
   if args.ad is None:
       print("Wrong Usage. Please use -h or --help flag for proper arguments")
   else:
       start_process(args.ad)

if __name__=="__main__":
    main()
