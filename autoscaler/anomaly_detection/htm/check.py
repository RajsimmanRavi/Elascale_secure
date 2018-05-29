import pandas as pd
from numenta_detector import NumentaDetector
import os
from prettytable import PrettyTable

def main(f_name):

    min_val = 0
    max_val = 100
    prob_index = 10

    detect = NumentaDetector(min_val, max_val, prob_index)
    detect.initialize()
    for index,row in ts.iterrows():
        value = row["value"]
        timestamp = row["timestamp"]
        score = detect.handleRecord(value,timestamp)

if __name__=="__main__":
    main()
