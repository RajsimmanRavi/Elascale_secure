import pandas as pd

def replace_timestamps(yahoo_file, nab_file):
    
    yahoo_ts = pd.read_csv(yahoo_file, parse_dates=True)
    nab_ts = pd.read_csv(nab_file, parse_dates=True)
    
    yahoo_copy = ts.copy(deep=True)
    yahoo_copy = ts_copy.drop('timestamp', axis=1)
    yahoo_copy['timestamp'] = pd.Series(nab_ts.timestamp[:len(yahoo_ts.index)], index=yahoo_copy.index)

    return yahoo_copy


