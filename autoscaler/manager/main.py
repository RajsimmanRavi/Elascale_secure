from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
#from autoscaler.policy.discrete import algorithm as discrete_alg
#from autoscaler.policy.adaptive import algorithm as adaptive_alg
from autoscaler.policy.adaptive import algorithm_micro as adaptive_alg

from autoscaler.anomaly_detection.relative_entropy.relative_entropy_detector import RelativeEntropyDetector
from autoscaler.anomaly_detection.htm.numenta_detector import NumentaDetector
from nupic.algorithms import anomaly_likelihood
import pandas as pd
import numpy as np
import sys

"""
RR: The code needs to be updated. I worked on getting results for CNSM, hence some hard-coded values.
RR: Will fix it soon
"""
def init_detects(elascale, min_val, max_cpu_val, max_net_val, prob_window, detect_type):
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
    #net_rx_util = float(stats["curr_netRx_util"])

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
    debug = "%s,%s,%s,%s,%s,%s\n" % (str(timestamp),cpu_util, net_tx_util, cpu_score, net_score, final)
    #util.write_to_file("results_spatial/"+service+".csv", debug)
    util.write_to_file("replicas_results_temporal/"+detect_type+"/"+service+".csv", debug)

    return final

def anomaly_detection(services, es, detects, detect_type):
    scores = []
    print("Services for Application Stack: %s " %(str(services)))

    if services:
        # Anomaly detection
        for item in services:
            micro_score = check_anomalies(item, es, "Micro", detects, detect_type)
            scores.append(micro_score)

        timestamp = pd.Timestamp.now()
        final_score = np.max(scores)
        current_replica = util.get_micro_replicas("iot_app_edge")
        write_score = "%s,%s,%s\n" % (str(timestamp),str(current_replica),final_score)
        #util.write_to_file("results_spatial/final.csv", write_score)
        util.write_to_file("replicas_results_temporal/"+detect_type+"/final.csv", write_score)

    return final_score


def main():

    anomaly_scores = []

    # This is the last index of the probationary period.
    # Remove all ground truth labels that come before it
    prob_window = 108 # If we evaluate the entire dataset for 2 hours 0.15 X 720 -- What I had for spatial, and trying for temporal

    min_val = 0.0 # Minimum cpu_util value
    max_cpu_val = 2e2 # Maximum cpu_util value
    max_net_val = 1e10 # Maximum Net_util value
    detect_type = sys.argv[1]

    elascale = Elascale()
    elascale.set_elastic_client()
    elascale.set_config()

    detects = init_detects(elascale, min_val, max_cpu_val, max_net_val, prob_window, detect_type)

    counter = 0
    sample_counter = 0 # This is for how many times
    while True:
        if counter == 800:
            sys.exit(1)

        elascale.set_config()

        # Get apps currently runnning
        apps = util.get_app_stacks()

        for app in apps:

            services = util.get_stack_services(app)
            final_score = anomaly_detection(services, elascale.es, detects, detect_type)
            #final_score = 0

            stats = util.get_stats("iot_app_edge", elascale.es, "Micro")
            cpu_util = float(stats['curr_cpu_util'])
            net_tx_util = float(stats["curr_netTx_util"])
            current_replica = util.get_micro_replicas("iot_app_edge")

            timestamp = pd.Timestamp.now()
            write_score = "%s,%s,%s,%s\n" % (str(timestamp),str(current_replica),cpu_util, net_tx_util)
            util.write_to_file("stats/final_with_htm.csv", write_score)

            if (final_score > (1 - 10e-5)):
                sample_counter = 1
                if int(current_replica) != 1:
                    print("replica not 1")
                    result = util.run_command("sudo docker service scale iot_app_edge="+str(1))
            else:
                if 0 < sample_counter <= 6:
                    print("in suspicion mode")

                    if int(current_replica) != 1:
                        print("replica not 1")
                        result = util.run_command("sudo docker service scale iot_app_edge="+str(1))

                    sample_counter += 1
                else:
                    sample_counter = 0

                    for micro in services:
                        if micro == "iot_app_edge": # just scale stream processor, nothing else
                            micro_status = util.check_status("Micro", micro, elascale.es)

                            curr_info = util.get_cpu_util(micro,elascale.es, "Micro", "high")
                            curr,thres = curr_info["util"], curr_info["thres"]

                            #timestamp = pd.Timestamp.now()
                            #write_score = "%s,%s,%s\n" % (str(timestamp),str(current_replica),curr)
                            #util.write_to_file("stats/final.csv", write_score)

                            if micro_status["status"] == "Normal":
                                print("Within CPU limit. Nothing to do for service: "+micro+"!\n")
                            else:
                                #macro_status = util.check_status("Macro", micro, elascale.es)
                                #discrete_alg(micro_status["status"], macro_status["status"], micro, macro_status["service"])
                                #adaptive_alg(micro, macro_status["service"], elascale.es)
                                adaptive_alg(micro,elascale.es) # For evaluating CNSM paper

            """
            if (final_score < (1 - 10e-5)):
                for micro in services:
                    micro_status = util.check_status("Micro", micro, elascale.es)

                    if micro_status["status"] == "Normal":
                        print("Within CPU limit. Nothing to do for service: "+micro+"!\n")
                    else:
                        macro_status = util.check_status("Macro", micro, elascale.es)
                        #discrete_alg(micro_status["status"], macro_status["status"], micro, macro_status["service"])
                        adaptive_alg(micro, macro_status["service"], elascale.es)
            """

        util.progress_bar(eng.MONITORING_INTERVAL)

        counter = counter + 1

if __name__=="__main__":
    main()
