import pandas as pd
from numenta_detector import NumentaDetector
import os
from prettytable import PrettyTable

def run(data):

    min_val = 0
    max_val = 100
    prob_index = 10

    detect = NumentaDetector(min_val, max_val, prob_index)
    detect.initialize()

    value = data["value"]
    timestamp = data["timestamp"]

    score = detect.handleRecord(value, timestamp)

    return score
