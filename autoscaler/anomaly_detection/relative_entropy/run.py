import pandas as pd 
from relative_entropy_detector import RelativeEntropyDetector
from plot import plot
import os
from prettytable import PrettyTable

def merge_windows(anomaly_windows):
    windows = []
    for i in range(len(anomaly_windows)):
        curr_start,curr_end = anomaly_windows[i][0], anomaly_windows[i][1]
        if i > 0:
            # check if curr_start is in previous index
            if windows[p][0] <= curr_start <= windows[p][1]:
                # If it is, them update the previous window's end index to curr end index
                # Hence, we're merging the windows
                windows[p][1] = curr_end
            else:
                # If not, simply add the current window
                windows.append([curr_start,curr_end])
                p = p + 1
        else:
            # Simply add the first window
            windows.append([curr_start,curr_end])
            p = i # have a pointer to last inserted window
    
    return windows    

def get_anomaly_windows(data_length, anomaly_indices):
    try:
        nab_window_len = int((0.1*data_length)/len(anomaly_indices))
    except:
        nab_window_len = int(0.1*data_length)
        pass 
    windows = []
    for index in sorted(anomaly_indices):
        start_index = (index)-(nab_window_len/2)
        end_index = (index)+(nab_window_len/2)  
        window = []
        window.append(start_index)
        window.append(end_index)
        windows.append(window)
    merged_windows = merge_windows(windows)
    return merged_windows

def get_probationary_index(cpu_util):
    # The first 15% of the data is considered proabtionary period and no FP/FN considered here
    # Hence, just provide the last index of this period, so we can eliminate detected indices falling
    # in this period
    prob_index = int(len(cpu_util)*0.15)    
    return prob_index        

def calc_precision(tp, fp):
    try:
        precision = tp/(tp+fp)
    except:
        precision = 0
        pass

    return precision

def calc_recall(tp, fn):
    try:
        recall = tp/(tp+fn)
    except:
        recall = 0
        pass
    return recall

def calc_f1(precision, recall):
    try:
        f1 = 2 * ((precision*recall)/(precision+recall))
    except:
        f1 = 0
        pass
    return f1

def get_true_positives(detected_indices, anomaly_windows):
    tp = 0

    for window in sorted(anomaly_windows):
        for index in sorted(detected_indices):
            start_index, end_index = window[0], window[1]
            if start_index <= index <= end_index:
                #print("True Positive: %s" % str(index))
                tp = tp + 1
                break
    
    #print("Number of True Positives: %s" % str(tp))
    return tp

def get_false_positives(detected_indices, anomaly_windows):
    fp = 0
    for index in sorted(detected_indices):
        counter = 0
        for window in sorted(anomaly_windows):
            start_index, end_index = window[0],window[1]
            if start_index <= index <= end_index:
                counter = counter + 1

        if counter == 0:
            #print("FP Index: %s" %str(index))
            fp = fp + 1
    #print("Number of False Positives: %s" % str(fp))
    return fp

def get_false_negatives(detected_indices, anomaly_windows):
    fn = 0 
    for window in sorted(anomaly_windows):
        counter = 0
        start_index, end_index = window[0],window[1]
        for index in sorted(detected_indices):
            if start_index <= index <= end_index:
                counter = counter + 1
        if counter == 0:
            #print("FN window: %s" % str(window))
            fn = fn + 1

    #print("Number of False Negatives: %s" % str(fn))
    return fn


def detect_anomalies(f_name):
    anomaly_scores = []
   
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

    detect = RelativeEntropyDetector(min_val, max_val)
    for value in cpu_util:
        score = detect.handleRecord(value)
        anomaly_scores.append(score)
    
    # Keep a list of indices that the algorithm detected as anomalies 
    detected_indices = []

    for i in range(len(anomaly_scores)):
        if anomaly_scores[i] != 0 and i > prob_index:
            detected_indices.append(i)
    
    #print("Ground Truth Anomalies: %s" % str(sorted(ground_truth_anomalies_indices)))
    #print("Detected Indices: %s" % str(sorted(detected_indices)))
    #print("Anomaly Windows: %s" % str(sorted(anomaly_windows)))
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

    folder = "/home/perplexednoob/Documents/CNSM/yahoo/A3Benchmark"
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
