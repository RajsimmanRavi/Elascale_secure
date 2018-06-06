from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
from autoscaler.policy.discrete import algorithm as discrete_alg
from autoscaler.policy.adaptive import algorithm as adaptive_alg
#from autoscaler.anomaly_detection.relative_entropy.relative_entropy_detector import RelativeEntropyDetector
from autoscaler.anomaly_detection.htm.numenta_detector import NumentaDetector
from nupic.algorithms import anomaly_likelihood
import pandas as pd
from scipy.stats import norm
from scipy.ndimage.filters import gaussian_filter
import numpy as np
import math

def init_detects(elascale, min_val, max_cpu_val, max_net_val, prob_window):
    services = {}

    for micro in elascale.micro_config.sections():

        # HTM
        services[micro,"cpu"] = NumentaDetector(min_val, max_cpu_val, prob_window)
        services[micro,"cpu"].initialize()

        services[micro,"net"] = NumentaDetector(min_val, max_net_val, prob_window)
        services[micro,"net"].initialize()

    for macro in elascale.macro_config.sections():

        # HTM
        services[macro,"cpu"] = NumentaDetector(min_val, max_cpu_val, prob_window)
        services[macro,"cpu"].initialize()

        services[macro,"net"] = NumentaDetector(min_val, max_net_val, prob_window)
        services[macro,"net"].initialize()

        services[macro,"final"] = NumentaDetector(0, 1, prob_window)
        services[macro,"final"].initialize()

    return services

def write_to_file(service, data):

    with open('results/'+service+'.csv', 'a+') as file:
        file.write(data)


def check_anomalies(service, es, service_type, detects):
    stats = util.get_stats(service, es, service_type)
    cpu_util = float(stats['curr_cpu_util'])
    net_tx_util = float(stats["curr_netTx_util"])
    #net_rx_util = float(stats["curr_netRx_util"])

    timestamp = pd.Timestamp.now()

    # This utilize HTM
    # It returns tuple (finalscore, raw_score). We care about only rawscore
    cpu_score = detects[service,"cpu"].handleRecord(cpu_util, timestamp)[0]
    net_score = detects[service,"net"].handleRecord(net_tx_util, timestamp)[0]

    #check = "timestamp: %s service: %s cpu_score: %s net_score: %s\n" %(timestamp, service, cpu_score, net_score)
    #print(check)
    #with open('results/check.csv', 'a+') as file:
    #    file.write(check)

    avg = np.mean([cpu_score, net_score])
    debug = "%s,%s,%s,%s,%s,%s\n" % (str(timestamp),cpu_util, net_tx_util, cpu_score, net_score, avg)
    write_to_file(service, debug)

    return avg

def main():

    anomaly_scores = []

    # This is the last index of the probationary period.
    # Remove all ground truth labels that come before it
    prob_window = 60 # Testing... Hence 10 minute window

    min_val = 0.0 # Minimum cpu_util value
    max_cpu_val = 2e2 # Maximum cpu_util value
    max_net_val = 1e10 # Maximum Net_util value

    elascale = Elascale()
    elascale.set_elastic_client()
    elascale.set_config()

    detects = init_detects(elascale, min_val, max_cpu_val, max_net_val, prob_window)

    while True:

        elascale.set_config()

        # Get apps currently runnning
        apps = util.get_app_stacks()

        for app in apps:

            services = util.get_stack_services(app)
            print("Services for Application Stack %s: %s " %(app, str(services)))

            if services:
                for key, value in services.items():
                    scores = []
                    # key is node/macroservice and it contains a list
                    macro_score = check_anomalies(key, elascale.es, "Macro", detects)
                    scores.append(macro_score)
                    for item in value:
                        # item is microservice
                        micro_score = check_anomalies(item, elascale.es, "Micro", detects)
                        scores.append(micro_score)

                    timestamp = pd.Timestamp.now()
                    final_score = detects[key,"final"].handleRecord(np.mean(scores), timestamp)[0]
                    write_score = "%s,%s,%s\n" % (str(timestamp),key,final_score)
                    write_to_file("final/"+key, write_score)

            """
            if cpu_score < 0.95 and net_score < 0.95:
                micro_status = util.check_status("Micro", micro, elascale.es)

                if micro_status["status"] == "Normal":
                    print("Within CPU limit. Nothing to do for service: "+micro+"!\n")
                else:
                    macro_status = util.check_status("Macro", micro, elascale.es)
                    #discrete_alg(micro_status["status"], macro_status["status"], micro, macro_status["service"])
                    adaptive_alg(micro, macro_status["service"], elascale.es)

        """
        util.progress_bar(eng.MONITORING_INTERVAL)

if __name__=="__main__":
    main()
