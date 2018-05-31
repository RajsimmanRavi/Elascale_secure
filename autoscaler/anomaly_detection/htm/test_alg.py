import pandas as pd
from numenta_detector import NumentaDetector
import os
from prettytable import PrettyTable
from util import *

def detect_anomalies(f_name):
    anomaly_scores = []

    # For HTM, they require actual unix timestamps
    # Hence replace them with a NAB data file's timestamps
    replacement_file = "../NAB/data/realAWSCloudwatch/ec2_cpu_utilization_24ae8d.csv"
    ts = replace_timestamps(f_name, replacement_file)

    ts = pd.read_csv(f_name, parse_dates=True)
    times= ts["timestamp"].tolist()
    labels = ts["is_anomaly"].tolist()
    cpu_util = ts["value"].tolist()

    # This is the last index of the probationary period.
    # Remove all ground truth labels that come before it
    prob_index = get_probationary_index(cpu_util)

    ground_truth_anomalies_indices = [i for i, x in enumerate(labels) if x != 0 and i > prob_index]
    anomaly_windows = get_anomaly_windows(len(cpu_util), ground_truth_anomalies_indices)

    min_val = min(cpu_util)
    max_val = max(cpu_util)

    detect = NumentaDetector(min_val, max_val, prob_index)
    detect.initialize()
    for index,row in ts.iterrows():
        value = row["value"]
        timestamp = row["timestamp"]
        score = detect.handleRecord(value,timestamp)
        anomaly_scores.append(score[1]) # Get just the raw anomaly score
        #print(score)


    # Keep a list of indices that the algorithm detected as anomalies
    detected_indices = []

    for i in range(len(anomaly_scores)):
        # Since raw_score is a value anywhere between 0 and 1,
        # we label it as anomaly if raw_score crosses 0.5 threshold
        if anomaly_scores[i] > 0.5 and i > prob_index:
            detected_indices.append(i)

    print("Ground Truth Anomalies: %s" % str(sorted(ground_truth_anomalies_indices)))
    print("Detected Indices: %s" % str(sorted(detected_indices)))
    print("Anomaly Windows: %s" % str(sorted(anomaly_windows)))
    tp = get_true_positives(detected_indices, anomaly_windows)
    fp = get_false_positives(detected_indices, anomaly_windows)
    fn = get_false_negatives(detected_indices, anomaly_windows)

    tp = float(tp)
    fp = float(fp)
    fn = float(fn)
    precision = calc_precision(tp,fp)
    recall = calc_recall(tp,fn)
    f1 = calc_f1(precision, recall)

    x = PrettyTable()
    x.field_names = ["File", "Precision", "Recall", "F1"]
    x.add_row([f_name, precision, recall, f1])
    print(x)
    x.clear_rows()
    x.clear()
    #print("File: %s Precision: %s Recall: %s F1: %s " % (f_name, str(precision), str(recall), str(f1)))
    #plot(times, cpu_util, labels, anomaly_scores, anomaly_windows)

    score_dict = {
        "Precision": precision,
        "Recall": recall,
        "F1": f1
    }
    return score_dict

def main():
    precision = []
    recall = []
    f1 = []

    #f_name = "/home/perplexednoob/Documents/CNSM/yahoo/A1Benchmark/real_1.csv"
    #scores = detect_anomalies(f_name)

    folder = "/home/perplexednoob/Documents/CNSM/yahoo/A1Benchmark"
    for f_name in os.listdir(folder):
        if f_name.endswith(".csv"):
            scores = detect_anomalies(os.path.join(folder,f_name))
            precision.append(scores["Precision"])
            recall.append(scores["Recall"])
            f1.append(scores["F1"])

    avg_precision = sum(precision)/len(precision)
    avg_recall = sum(recall)/len(recall)
    avg_f1 = sum(f1)/len(f1)

    print("Average Precision (importance for False Positives): %s " % str(avg_precision))
    print("Average Recall (importance for False Negatives): %s " % str(avg_recall))
    print("Average F1 (importance for both): %s " % str(avg_f1))

if __name__=="__main__":
    main()
