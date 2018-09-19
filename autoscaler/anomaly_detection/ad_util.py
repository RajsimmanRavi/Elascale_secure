from autoscaler.anomaly_detection.relative_entropy.relative_entropy_detector import RelativeEntropyDetector
from autoscaler.anomaly_detection.htm.numenta_detector import NumentaDetector
import autoscaler.conf.engine_config as eng
from autoscaler import util
from nupic.algorithms import anomaly_likelihood
import pandas as pd
import numpy as np

def init_detects(elascale):

    min_cpu_val = eng.MIN_CPU_VAL
    max_cpu_val = eng.MAX_CPU_VAL
    max_net_val = eng.MAX_NET_VAL
    prob_window = eng.PROB_WINDOW

    services = {}

    for micro in elascale.micro_config.sections():

        # HTM
        services[micro,"cpu"] = NumentaDetector(min_cpu_val, max_cpu_val, prob_window)
        services[micro,"cpu"].initialize()

        services[micro,"net"] = NumentaDetector(min_cpu_val, max_net_val, prob_window)
        services[micro,"net"].initialize()

    return services

def check_anomalies(service, es, service_type, detects):
    stats = util.get_stats(service, es, service_type)
    cpu_util = float(stats['curr_cpu_util'])
    net_tx_util = float(stats["curr_netTx_util"])

    timestamp = pd.Timestamp.now()

    # It returns tuple (finalscore, raw_score). We care about only rawscore
    cpu_score = detects[service,"cpu"].handleRecord(cpu_util, timestamp)[0]
    net_score = detects[service,"net"].handleRecord(net_tx_util, timestamp)[0]

    final = np.max([cpu_score, net_score])

    return final

def anomaly_detection(services, es, detects):
    scores = []
    print("Services for Application Stack: %s " %(str(services)))

    if services:
        # Anomaly detection
        for item in services:
            micro_score = check_anomalies(item, es, "Micro", detects)
            scores.append(micro_score)

        timestamp = pd.Timestamp.now()
        final_score = np.max(scores)

    return final_score
