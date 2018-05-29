import pandas as pd
from autoscaler.anomaly_detection.relative_entropy.relative_entropy_detector import RelativeEntropyDetector
import os
from prettytable import PrettyTable
from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
from autoscaler.policy.discrete import algorithm as discrete_alg
from autoscaler.policy.adaptive import algorithm as adaptive_alg

def init_detects(elascale, min_val, max_val, prob_window):
    services = {}

    for micro in elascale.micro_config.sections():
        services[micro] = RelativeEntropyDetector(min_val, max_val, prob_window)

    for macro in elascale.macro_config.sections():
        services[macro] = RelativeEntropyDetector(min_val, max_val, prob_window)

    return services


def main():

    anomaly_scores = []

    # This is the last index of the probationary period.
    # Remove all ground truth labels that come before it
    prob_window = 6 # Testing... 18 samples with frequency 1/10 seconds. Hence 3 minute window

    min_val = 0.0 # Minimum cpu_util value
    max_val = 100.0 # Maximum cpu_util value

    #gevent.signal(signal.SIGQUIT, gevent.kill)

    elascale = Elascale()
    elascale.set_elastic_client()

    elascale.set_config()

    detects = init_detects(elascale, min_val, max_val, prob_window)

    while True:

        elascale.set_config()

        #threads = []
        for micro in elascale.micro_config.sections():
            stats = util.get_stats(micro, elascale.es, "Micro")
            cpu_util = float(stats['curr_cpu_util'])
            score = detects[micro].handleRecord(cpu_util)

            print("MicroService: %s Current Stat: %s Score: %s" % (str(micro), str(cpu_util), str(score)))

        for macro in elascale.macro_config.sections():
            macro_status = util.get_stats(macro, elascale.es, "Macro")
            cpu_util = float(stats['curr_cpu_util'])
            score = detects[macro].handleRecord(cpu_util)

            print("MacroService: %s Current Stat: %s Score: %s" % (str(macro),str(cpu_util), str(score)))

        util.progress_bar(eng.MONITORING_INTERVAL)

if __name__=="__main__":
    main()
