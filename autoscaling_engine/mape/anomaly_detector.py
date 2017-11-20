import warnings
import itertools
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.ar_model import AR

warnings.filterwarnings("ignore") # specify to ignore warning messages

def load_data(f_name):
    print(f_name)
    data = pd.read_csv(f_name)
    # Convert date to proper format
    data['Date'] = pd.to_datetime(data['Date'],format="%Y-%m-%dT%H:%M:%S.%fZ")
    indexed_df = data.set_index('Date')

    ts = indexed_df['Value']

    if "net" in f_name:
        # normalize and add 1 to make it positive
        ts = (ts - ts.mean()) / (ts.std())+1

    ts_diff = ts
    ts_diff.dropna(inplace=True)

    y = ts

    return y


def find_anomaly(errors):
    for key, val in errors.items():
        # Get the last item and remove the whitespaces.
        error_diff = float(val.split(":")[-1].strip())
        if error_diff > 0.45:
            #print("Found anomaly at %s"% (val))
            return (str(key)+": "+val)
    return False

def find_anomaly_network(errors):
    for key, val in errors.items():
        # Get the last item and remove the whitespaces.
        error_diff = float(val.split(":")[-1].strip())
        if error_diff > 1.0:
            #print("Found anomaly at %s"% (val))
            return (str(key)+": "+val)
    return False

def ar_model(data):

    # There are around 320 samples/hour
    # So, we can take last 2 hours worth of training/testing samples (around 640)
    # So with 80/20 approach We'll take 520 samples for training and 120 for testing
    X = data.values
    test_timestamps = data.keys()[len(X)-60:]
    train, test = X[1:len(X)-60], X[len(X)-60:]

    # train autoregression
    model = AR(train)
    model_fit = model.fit()

    predictions = model_fit.predict(start=len(train), end=len(train)+len(test)-1, dynamic=False)
    errors = {}
    for i in range(len(predictions)):
        diff = np.sqrt(np.square(predictions[i] - test[i]))
        errors[test_timestamps[i]] = "Predicted: "+str(predictions[i])+", Observed: "+str(test[i])+", Diff: "+str(diff)
        print('predicted=%f, observed=%f. Diff=%f, datetime=%s' % (predictions[i], test[i], diff, test_timestamps[i]))

    mse = mean_squared_error(test, predictions)
    #print('Test MSE: %.3f' % mse)

    return errors

def detect_anomaly(f_name):

    y = load_data(f_name)
    errors = ar_model(y)

    if "net" in f_name:
        report = find_anomaly_network(errors)
    else:
        report = find_anomaly(errors)


    if (report != False):
        #print("Do not scale!")
        return report
    else:
        #print("It's okay! It's safe to scale")
        return False



