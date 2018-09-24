from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
from autoscaler.policy.discrete import discrete_micro, discrete_macro
from autoscaler.policy.adaptive import adaptive_micro, adaptive_macro
#import pandas as pd
#import numpy as np
#import sys
import argparse

parser = argparse.ArgumentParser(description="*** Autoscaler Arguments ***")
parser.add_argument('-ad', '--ad', help='Enable Anomaly Detection (True/False). Defaults to False', type=util.str2bool, nargs='?', default=False)
parser.add_argument('-p', '--policy', help='Discrete or Adaptive Policy Enable Anomaly Detection (d/a). Defaults to "d"', type=str, nargs='?', default='d')
args = parser.parse_args()

def start_process():
    elascale = Elascale()
    elascale.set_elastic_client()
    elascale.set_config()

    # The first argument (Bool) mentions whether enable anomaly detection or not
    enable_ad = args.ad

    if enable_ad == True:
        print("Anomaly Detection Enabled")
        from autoscaler.anomaly_detection import ad_util
        anomaly_scores = []
        detects = ad_util.init_detects(elascale)
        sample_counter = 0 # This is for how many times in investigation period

    while True:
        elascale.set_config()

        # Get apps currently runnning
        apps = util.get_app_stacks()
        print("MONITORING APPS: %s" %(str(apps)))
        for app in apps:

            services = util.get_stack_services(app)
            nodes = util.get_stack_nodes(app)

            #print("app: %s nodes: %s" %(app,nodes))

            if enable_ad:
                final_score = ad_util.anomaly_detection(services, elascale.es, detects)

                if (final_score > (1 - 10e-5)):
                    print("--- Entered investigation period... ---")
                    sample_counter = 1
                    util.remove_extra_replicas(app)
                else:
                    if 0 < sample_counter <= eng.INVESTIGATION_PHASE_LENGTH:
                        print("--- Still in investigation period... ---")
                        util.remove_extra_replicas(app)
                        sample_counter += 1
                    else:
                        print("--- Exiting investigation period and start scaling procedure... ---")
                        sample_counter = 0
                        scale(services, elascale)
            else:
                # Anomaly detection not enabled, go straight to scaling policy
                scale(services, nodes, elascale)

        util.progress_bar(eng.MONITORING_INTERVAL)

def scale(services, nodes, elascale):
    for micro in services:
        if args.policy == 'd':
            discrete_micro(micro, elascale.es)
        else:
            adaptive_micro(micro, elascale.es)

    for macro in nodes:
        if args.policy == 'd':
            discrete_macro(macro, elascale.es)
        else:
            adaptive_macro(macro, elascale.es)

def main():
    print(util.run_command("figlet -f big Elascale"))
    print(util.run_command("python2.7 -m autoscaler.manager.main -h"))

    start_process()

if __name__=="__main__":
    main()
