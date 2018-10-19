from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
from autoscaler.policy.discrete import discrete_micro, discrete_macro
from autoscaler.policy.adaptive import adaptive_micro, adaptive_macro
import argparse
import os

# For eDoS Mitigation Evaluation Results

overall_header = "Timestamp,Sensor CPU Usage,Sensor Network Transmitted Bytes,Sensor Replicas,"
overall_header += "REST API CPU Usage,REST API Network Transmitted Bytes,REST API Sensor Replicas,"
overall_header += "DB CPU Usage,DB Network Transmitted Bytes,DB Replicas,Anomaly Score\n"
util.recreate_log_file(eng.LOGGING_FILE,overall_header)

"""
# Not needed anymore. Verified HTM and RE are using all the microservices for anomaly scores
# If you do need to uncomment it, then you need to uncomment saving stats in anomaly_detection/ad_util.py

separate_stats_header = "Timestamp,CPU Usage,Network Transmitted Bytes,CPU Anomaly Score,Network Anomaly Score,Final Anomaly Score\n"
util.recreate_log_file("/home/ubuntu/Elascale_secure/tests/cnsm/iot_app_rest_api_stats.csv", separate_stats_header)
util.recreate_log_file("/home/ubuntu/Elascale_secure/tests/cnsm/iot_app_db_stats.csv", separate_stats_header)
"""

parser = argparse.ArgumentParser(description="*** Elascale Autoscaler Arguments ***")
parser.add_argument('-ad', '--ad', help='Enable Anomaly Detection? (arg: bool). Default: False', type=util.str2bool, nargs='?', default=False)
parser.add_argument('-ad_alg', '--ad_alg', help='Anomaly Detection Type: "re" or "htm". Default: "htm"', type=str, nargs='?', default='htm')
parser.add_argument('-macro', '--macro', help='Enable Autoscaling Macroservices? (arg: bool). Default: False', type=util.str2bool, nargs='?', default=False)
parser.add_argument('-p', '--policy', help='Discrete or Adaptive Policy? (arg: "d"/"a"/"none"). "none" is Monitor mode. Default: "d"', type=str, nargs='?', default='d')
args = parser.parse_args()

def start_process():

    elascale = Elascale()
    elascale.set_elastic_client()
    elascale.set_config()

    # The first argument (Bool) mentions whether enable anomaly detection or not
    enable_ad = args.ad
    enable_macro = args.macro

    if enable_ad == True:
        print("Anomaly Detection Enabled")
        from autoscaler.anomaly_detection import ad_util
        anomaly_scores = []
        detects = ad_util.init_detects(elascale, args.ad_alg)
        sample_counter = 0 # This is for how many times in investigation period

    while True:
        # Update the config based on currently running services
        elascale.set_config()

        # Get apps currently runnning
        apps = util.get_app_stacks()
        print("MONITORING APPS: %s" %(str(apps)))
        for app in apps:

            # Get microservices for that specific application
            services = util.get_stack_services(app,True)

            # If Anomaly detection is enabled
            if enable_ad:
                final_score = ad_util.anomaly_detection(services, elascale.es, detects, args.ad_alg)

                if (final_score > eng.ANOMALY_THRESHOLD):
                    print("--- Entered investigation period... ---")
                    sample_counter = 1
                    util.remove_extra_resources(app)
                else:
                    if 0 < sample_counter <= eng.INVESTIGATION_PHASE_LENGTH:
                        print("--- Still in investigation period... ---")
                        util.remove_extra_resources(app)
                        sample_counter += 1
                    else:
                        print("--- Exiting investigation period and start scaling procedure... ---")
                        sample_counter = 0
                        micro_scale(services, elascale)
            else:
                micro_scale(services, elascale)
                if enable_macro:
                    nodes = util.get_stack_nodes(app)
                    macro_scale(nodes, elascale)

        """
        # This is for collecting stats for evaluation
        stats = util.get_stats("iot_app_rest_api", elascale.es, "Micro")
        cpu_util = float(stats['curr_cpu_util'])
        net_tx_util = float(stats["curr_netTx_util"])

        write_stats = "%s,%s" %(str(cpu_util),str(net_tx_util),str(util.get_micro_replicas("iot_app_sensor")),str(util.get_micro_replicas("iot_app_rest_api")))
        logger.warning(write_stats)
        """
        util.collect_stats(elascale.es)

        util.progress_bar(eng.MONITORING_INTERVAL)

def micro_scale(services, elascale):
    for micro in services:
        #logger.warning("%s" %(str(util.get_micro_replicas(micro))))
        if args.policy == 'd':
            discrete_micro(micro, elascale.es)
        elif args.policy == 'a':
            adaptive_micro(micro, elascale.es)
        else:
            print("Enabled Monitor Mode. Not Autoscaling...")

def macro_scale(nodes, elascale):
    for macro in nodes:
        if args.policy == 'd':
            discrete_macro(macro, elascale.es)
        elif awgs.policy == 'a':
            adaptive_micro(macro, elascale.es)
        else:
            print("Enabled Monitor Mode. Not Autoscaling...")

def main():
    print(util.run_command("figlet -f big Elascale"))
    print(util.run_command("python2.7 -m autoscaler.manager.main -h"))

    start_process()

if __name__=="__main__":
    main()
