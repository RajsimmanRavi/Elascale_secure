from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
from autoscaler.policy.discrete import algorithm as discrete_alg
from autoscaler.policy.adaptive import algorithm as adaptive_alg
import pandas as pd
from numenta_detector import NumentaDetector
import os

def main():

    elascale = Elascale()
    elascale.set_elastic_client()

    while True:
        elascale.set_config()

        for micro in elascale.micro_config.sections():
            cpu_stats = util.get_stats(micro, elascale.es, "Micro")
            print(float(cpu_stats["curr_cpu_util"]))


        for macro in elascale.macro_config.sections():
            cpu_stats = util.get_stats(micro, elascale.es, "Micro")
            print(float(cpu_stats["curr_cpu_util"]))


    min_val = 0
    max_val = 100
    prob_index = 10

    detect = NumentaDetector(min_val, max_val, prob_index)
    detect.initialize()
    for index,row in ts.iterrows():
        value = row["value"]
        timestamp = row["timestamp"]
        score = detect.handleRecord(value,timestamp)

        util.progress_bar(eng.MONITORING_INTERVAL)

if __name__=="__main__":
    main()
