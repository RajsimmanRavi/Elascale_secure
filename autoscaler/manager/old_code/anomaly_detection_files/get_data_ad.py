import warnings
import itertools
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.ar_model import AR
from collections import OrderedDict

warnings.filterwarnings("ignore") # specify to ignore warning messages

def load_data(f_name):
    print(f_name)
    data = pd.read_csv(f_name)
    # Convert date to proper format
    data['Date'] = pd.to_datetime(data['Date'],format="%Y-%m-%dT%H:%M:%S.%fZ")
    indexed_df = data.set_index('Date')

    ts = indexed_df['Value']

    """
    if "net" in f_name:
        # normalize and add 1 to make it positive
        ts = (ts - ts.mean()) / (ts.std())+1
    """

    if "net" in f_name:
        #print("Before Consolidation of Network Interfaces, Length of Raw Data: %d" %len(ts))
        ts = ts.groupby(ts.index).sum()
        #print("After Consolidateion of Network Interfaces, Length of Raw Data: %d" %len(ts))

    ts_diff = ts
    ts_diff.dropna(inplace=True)

    y = ts

    #print("Raw Data Length: %d" % len(y))

    # We get 10 sec samples. Hence, take average per min buckets
    y = y.resample('60S').mean()

    #print("After sample/min, Data length: %d" % len(y))

    # Make sure it is divisible by 10 and remove any last remaining ones
    # This is useful and important when cleaning training data
    num_residuals = len(y) % 10
    #print("Number of residuals: %d" %(num_residuals))
    y = y[num_residuals:]

    #print("After making it divisible by 10, Data Length: %d" %len(y))
    y = y.fillna(y.bfill())


    #This is for printing the values for CPU Utilization
    with pd.option_context('display.max_rows', None, 'display.max_columns', 3):
        print(y)

    return y


def find_anomaly(errors):
    for key, val in errors.items():
        # Get the last item and remove the whitespaces.
        error_diff = round(float(val.split(":")[-1].strip()),2)
        print("Error_diff: %f" % error_diff)
        if float(error_diff) > float(0.15):
            print("Found anomaly at %s because diff > 0.45!"% (val))
            return (str(key)+": "+val)
        else:
            print("Found no anomalies for CPU!")
    return False

def find_anomaly_network(errors):
    for key, val in errors.items():
        # Get the last item and remove the whitespaces.
        error_diff = round(float(val.split(":")[-1].strip()),2)
        print("Error_diff: %f" % error_diff)
        if float(error_diff) > float(1.0):
            print("Found anomaly at %s because diff > 1.0!"% (val))
            return (str(key)+": "+val)
        else:
            print("Found no anomalies for Network!")
    return False

def clean_data(train):
    #print("Length of Training Data: %d " % len(train))
    backup = np.array(train, copy=True)
    chunks = [train[x:x+10] for x in range(0, len(train), 10)]

    """
    for i in range(len(chunks)):
        print(chunks[i])
    """

    num_cols = len(chunks[0]) # Get one row
    num_rows = len(chunks)

    results = num_cols * [0]
    for col in range(num_cols):
        for row in range(num_rows):
            results[col] += chunks[row][col]

    n_elems = float(num_rows)
    mean_results = [s/n_elems for s in results]

    #print("Mean Values for a pattern: %s" % str(mean_results))

    # Check if each element's difference from the mean > 10%
    # If it is, then replace the value as mean
    for col in range(num_cols):
        for row in range(num_rows):
            diff = abs(chunks[row][col] - mean_results[col])
            if diff > 0.15:
                #print("[REQUIRES CHANGE - ERROR > 15%%]: chunks[%d][%d]: %f, mean_results[%d]: %f. Diff: %f" %(row, col, chunks[row][col], col, mean_results[col], diff))
                chunks[row][col] = mean_results[col]


    final_train = np.array(chunks)
    final_train = final_train.ravel()

    #print(final_train)
    #print(backup)

    #plt.plot(backup)
    #plt.plot(final_train, color='red')
    #plt.show()

    return final_train


def ar_model(data):

    # There are around 320 samples/hour
    # So, we can take last 2 hours worth of training/testing samples (around 640)
    # So with 80/20 approach We'll take 520 samples for training and 120 for testing
    X = data.values
    test_timestamps = data.keys()[len(X)-10:]
    train, test = X[0:len(X)-10], X[len(X)-10:]

    """
    test_timestamps = data.keys()[len(X)-60:]
    train, test = X[0:len(X)-60], X[len(X)-60:]
    """
    # Before Training the model, let's clean the data
    train = clean_data(train)

    # train autoregression
    model = AR(train)
    model_fit = model.fit()

    predictions = model_fit.predict(start=len(train), end=len(train)+len(test)-1, dynamic=False)
    errors = {}
    for i in range(len(predictions)):
        diff = np.sqrt(np.square(predictions[i] - test[i]))
        errors[test_timestamps[i]] = "Predicted: "+str(predictions[i])+", Observed: "+str(test[i])+", Diff: "+str(diff)
        #print('predicted=%f, observed=%f. Diff=%f, datetime=%s' % (predictions[i], test[i], diff, test_timestamps[i]))

    mse = mean_squared_error(test, predictions)
    print('Test MSE: %.3f' % mse)

    return errors

def detect_anomaly(f_name):

    y = load_data(f_name)
    #print(y.tail(5))
    """
    errors = ar_model(y)

    ## We need to only give the last sample of prediction to check whether it's an anomaly or not
    ## Hence, we do some list ordering and get the last sample
    # First, order them based on timestamp key
    od = OrderedDict(sorted(errors.items(), key=lambda t: t[0]))
    # Get the last one to get the most recent data
    key = next(reversed(od))
    # Create a regular dict to pass it to function
    final_error = {key: od[key]}

    #print(od)
    print(final_error)

    if "network" in f_name:
        report = find_anomaly_network(final_error)
    else:
        report = find_anomaly(final_error)


    if (report != False):
        #print("Do not scale!")
        return report
    else:
        #print("It's okay! It's safe to scale")
        return False
    """


