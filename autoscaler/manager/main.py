from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
from autoscaler.policy.discrete import algorithm as discrete_alg
from autoscaler.policy.adaptive import algorithm as adaptive_alg
from autoscaler.anomaly_detection.relative_entropy.relative_entropy_detector import RelativeEntropyDetector
from autoscaler.anomaly_detection.htm.numenta_detector import NumentaDetector
import pandas as pd
from scipy.stats import norm
from scipy.ndimage.filters import gaussian_filter
import numpy as np
import math

def anomaly_likelihood(scores):
    scores = np.array(scores)
    mean, std = np.mean(scores), np.std(scores)

    print("Mean: %s Std: %s" % (mean, std))
    try:
        likelihood = 1
        for score in scores:
            cdf = norm.cdf(score, loc=mean, scale=std)
            smoothed_cdf = 2*gaussian_filter(1-cdf, std)
            likelihood = likelihood * smoothed_cdf

        final_score = 1 - likelihood
    except:
        final_score = 0
        pass

    if math.isnan(final_score):
        final_score = 0

    return final_score

def init_detects(elascale, min_val, max_cpu_val, max_net_val, prob_window):
    services = {}

    for micro in elascale.micro_config.sections():

        #services[micro] = RelativeEntropyDetector(min_val, max_val, prob_window)

        services[micro,"cpu"] = NumentaDetector(min_val, max_cpu_val, prob_window)
        services[micro,"cpu"].initialize()

        services[micro,"net"] = NumentaDetector(min_val, max_net_val, prob_window)
        services[micro,"net"].initialize()

    for macro in elascale.macro_config.sections():
        #services[macro] = RelativeEntropyDetector(min_val, max_val, prob_window)

        services[macro,"cpu"] = NumentaDetector(min_val, max_cpu_val, prob_window)
        services[macro,"cpu"].initialize()

        services[macro,"net"] = NumentaDetector(min_val, max_net_val, prob_window)
        services[macro,"net"].initialize()

    return services

def check_anomalies(service, es, service_type, detects):
    stats = util.get_stats(service, es, service_type)
    cpu_util = float(stats['curr_cpu_util'])
    net_tx_util = float(stats["curr_netTx_util"])
    #net_rx_util = float(stats["curr_netRx_util"])

    timestamp = pd.Timestamp.now()

    # This utilize HTM
    # It returns tuple (rawscore, finalscore). We care about only rawscore
    cpu_score = detects[service,"cpu"].handleRecord(cpu_util, timestamp)[0]
    net_score = detects[service,"net"].handleRecord(net_tx_util, timestamp)[0]

    # This utilizes Relative Entropy
    #score = detects[micro].handleRecord(cpu_util)

    likelihood = anomaly_likelihood([cpu_score, net_score])

    print("Service: %s Curr CPU: %s Curr Net_Tx: %s CPU Score: %s Net Score: %s Likelihood: %s " % (service, cpu_util, net_tx_util, cpu_score, net_score, likelihood))

    return likelihood

def main():

    anomaly_scores = []

    # This is the last index of the probationary period.
    # Remove all ground truth labels that come before it
    prob_window = 6 # Testing... 18 samples with frequency 1/10 seconds. Hence 3 minute window

    min_val = 0.0 # Minimum cpu_util value
    max_cpu_val = 1e2 # Maximum cpu_util value
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

            micro_scores = []
            macro_scores = []

            services = util.get_stack_services(app)
            print("Microservices for Application Stack %s: %s " %(app, str(services)))

            if services:
                for micro in services:
                    score = check_anomalies(micro, elascale.es, "Micro", detects)
                    micro_scores.append(score)

                micro_likelihood = anomaly_likelihood(micro_scores)
                print("Final Microservices Anomaly Likelihood: %s" % micro_likelihood)

                nodes = util.get_stack_nodes(app)
                for macro in nodes:
                    score = check_anomalies(macro, elascale.es, "Macro", detects)
                    macro_scores.append(score)

                macro_likelihood = anomaly_likelihood(macro_scores)
                print("Final Macroservices Anomaly Likelihood: %s" % macro_likelihood)

                final_score = anomaly_likelihood([micro_likelihood, macro_likelihood])
                print("Final score: %s" % final_score)

            """
                stats = util.get_stats(micro, elascale.es, "Micro")
                cpu_util = float(stats['curr_cpu_util'])
                net_tx_util = float(stats["curr_netTx_util"])
                #net_rx_util = float(stats["curr_netRx_util"])

                timestamp = pd.Timestamp.now()

                # This utilize HTM
                # It returns tuple (rawscore, finalscore). We care about only rawscore
                cpu_score = detects[micro,"cpu"].handleRecord(cpu_util, timestamp)[0]
                net_score = detects[micro,"net"].handleRecord(net_tx_util, timestamp)[0]

                # This utilizes Relative Entropy
                #score = detects[micro].handleRecord(cpu_util)

                print("MicroService: %s Current Stat: %s CPU Score: %s Net Score: %s" % (micro, cpu_util, cpu_score, net_score))
                """
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
        """
        for macro in elascale.macro_config.sections():
            macro_status = util.get_stats(macro, elascale.es, "Macro")
            cpu_util = float(stats['curr_cpu_util'])
            score = detects[macro].handleRecord(cpu_util)

            print("MacroService: %s Current Stat: %s Score: %s" % (str(macro),str(cpu_util), str(score)))
        """

        util.progress_bar(eng.MONITORING_INTERVAL)

if __name__=="__main__":
    main()
