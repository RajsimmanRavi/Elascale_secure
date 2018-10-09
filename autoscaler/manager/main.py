from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
from autoscaler.policy.discrete import discrete_micro, discrete_macro
from autoscaler.policy.adaptive import adaptive_micro, adaptive_macro
import argparse
import logging
from logging.handlers import RotatingFileHandler

formatter = logging.Formatter('%(asctime)s,%(message)s',"%Y-%m-%d %H:%M")
logger = logging.getLogger(__name__)
handler = RotatingFileHandler(eng.LOGGING_FILE, maxBytes=5*1024*1024, backupCount=10)
handler.setFormatter(formatter)
logger.addHandler(handler)


parser = argparse.ArgumentParser(description="*** Elascale Autoscaler Arguments ***")
parser.add_argument('-ad', '--ad', help='Enable Anomaly Detection? (arg: bool). Default: False', type=util.str2bool, nargs='?', default=False)
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
        detects = ad_util.init_detects(elascale)
        sample_counter = 0 # This is for how many times in investigation period

    while True:
        # Update the config based on currently running services
        elascale.set_config()

        # Get apps currently runnning
        apps = util.get_app_stacks()
        print("MONITORING APPS: %s" %(str(apps)))
        for app in apps:

            # Get macro/microservices for that specific application
            services = util.get_stack_services(app)


            # If Anomaly detection is enabled
            if enable_ad:
                final_score = ad_util.anomaly_detection(services, elascale.es, detects)

                if (final_score > eng.ANOMALY_THRESHOLD):
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
                        micro_scale(services, elascale)
            else:
                micro_scale(services, elascale)
                if enable_macro:
                    nodes = util.get_stack_nodes(app)
                    macro_scale(nodes, elascale)

        # This is for collecting stats for evaluation
        curr_info = util.get_cpu_util("iot_app_rest_api", elascale.es, "Micro", "high")
        curr,thres = curr_info["util"], curr_info["thres"]
        cpu_stats = "%s,%s" %(str(curr), str(util.get_micro_replicas("iot_app_rest_api")))
        logger.warning(cpu_stats)

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
