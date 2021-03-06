from autoscaler.anomaly_detection.relative_entropy.relative_entropy_detector import RelativeEntropyDetector
from autoscaler.anomaly_detection.htm.numenta_detector import NumentaDetector
import autoscaler.conf.engine_config as eng
from autoscaler import util
from nupic.algorithms import anomaly_likelihood
import pandas as pd
import numpy as np


## RR: You'll need this for evaluation for Thesis.

"""
RR: The code needs to be updated. I worked on getting results for CNSM, hence some hard-coded values.
RR: Will fix it soon
"""
def init_detects(elascale, detect_type):

    prob_window = eng.PROB_WINDOW
    min_val = eng.MIN_CPU_VAL
    max_cpu_val = eng.MAX_CPU_VAL
    max_net_val = eng.MAX_NET_VAL
    services = {}

    for micro in elascale.micro_config.sections():

        if detect_type == "re":
            # Relative Entropy
            services[micro,"cpu"] = RelativeEntropyDetector(min_val, max_cpu_val, prob_window)
            services[micro,"net"] = RelativeEntropyDetector(min_val, max_net_val, prob_window)
        else:
            # HTM
            services[micro,"cpu"] = NumentaDetector(min_val, max_cpu_val, prob_window)
            services[micro,"cpu"].initialize()

            services[micro,"net"] = NumentaDetector(min_val, max_net_val, prob_window)
            services[micro,"net"].initialize()

    return services

def check_anomalies(service, es, service_type, detects, detect_type):
    stats = util.get_stats(service, es, service_type)
    cpu_util = float(stats['curr_cpu_util'])
    net_tx_util = float(stats["curr_netTx_util"])

    timestamp = pd.Timestamp.now()

    if detect_type == "re":
        # This utilizes Relative Entropy
        cpu_score = detects[service,"cpu"].handleRecord(cpu_util)
        net_score = detects[service,"net"].handleRecord(net_tx_util)
    else:
        # This utilize HTM
        # It returns tuple (finalscore, raw_score). We care about only rawscore
        cpu_score = detects[service,"cpu"].handleRecord(cpu_util, timestamp)[0]
        net_score = detects[service,"net"].handleRecord(net_tx_util, timestamp)[0]

    final = np.max([cpu_score, net_score])

    # Verified that this is working. If you do uncomment, make sure you re-create files (top of manager/main.py)
    #debug = "%s,%s,%s,%s,%s,%s\n" % (str(timestamp),cpu_util, net_tx_util, cpu_score, net_score, final)
    #util.write_to_file("/home/ubuntu/Elascale_secure/tests/cnsm/"+service+"_stats.csv", debug)

    return final



def anomaly_detection(services, es, detects, detect_type):
    scores = []
    print("Services for Application Stack: %s " %(str(services)))

    if services:
        # Anomaly detection
        for item in services:
            #if item != "iot_app_sensor":
            micro_score = check_anomalies(item, es, "Micro", detects, detect_type)
            scores.append(micro_score)

        final_score = np.max(scores)
        file_name = "/var/log/elascale/"+detect_type+"_stats.csv"
        util.collect_stats(file_name, es, final_score)

    return final_score
