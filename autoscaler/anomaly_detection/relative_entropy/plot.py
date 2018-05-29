import plotly
from plotly import tools
from plotly.graph_objs import Scatter, Figure, Layout

def plot(times, cpu_util, labels, anomaly_scores, anomaly_windows):
    #scale labels and anomaly scores to the max of cpu_util, so it plots nicely
    labels = [i * max(cpu_util) for i in labels]
    anomaly_scores = [i * max(cpu_util) for i in anomaly_scores]
    fig = tools.make_subplots(rows=2, cols=1, print_grid=True)

    trace1 = Scatter(
        x=times,
        y=cpu_util,
        name='CPU UTILIZATION OF AN AWS SERVER'
    )
    trace2 = Scatter(
        x=times,
        y=labels,
        name='GROUND TRUTH OF ANOMALIES',
        yaxis='y2'
    )
    
    trace3 = Scatter(
        x=times,
        y=anomaly_scores,
        name='ANOMALY SCORES BY TUKEY AND RELATIVE ENTROPY',
        yaxis='y2'
    )

    # We want a probabitionary period which is 15% of data length
    prob_period_index = int(len(cpu_util)*0.15)    
    prob_period = Scatter(
        x=times[0:prob_period_index],
        y=[max(cpu_util) for x in range(prob_period_index-1)],
        name='Probationary Period',
        fill='tozeroy'
    )

    fig.append_trace(trace1, 1,1)
    fig.append_trace(trace2, 1,1)
    fig.append_trace(trace1, 2,1)
    fig.append_trace(trace3, 2,1)
    fig.append_trace(prob_period, 2,1)
    
    # We need to build anomaly windows which is -5 to +5 of ground truth anomaly
    anomaly_indices = [i for i, x in enumerate(labels) if x != 0]
    for an_window in anomaly_windows:
        start_index, end_index = an_window[0], an_window[1]
        window = Scatter(
            x=times[start_index:end_index+1],
            y=[max(cpu_util) for x in range(end_index-start_index)],
            name='Anomaly Window',
            fill='tozeroy',
        )
        fig.append_trace(window, 2,1)
    
    plotly.offline.plot(fig)
