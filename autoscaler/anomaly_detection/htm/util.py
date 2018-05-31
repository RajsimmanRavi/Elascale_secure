import pandas as pd

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

def replace_timestamps(yahoo_file, nab_file):

    yahoo_ts = pd.read_csv(yahoo_file, parse_dates=True)
    nab_ts = pd.read_csv(nab_file, parse_dates=True)

    yahoo_copy = ts.copy(deep=True)
    yahoo_copy = ts_copy.drop('timestamp', axis=1)
    yahoo_copy['timestamp'] = pd.Series(nab_ts.timestamp[:len(yahoo_ts.index)], index=yahoo_copy.index)

    return yahoo_copy
