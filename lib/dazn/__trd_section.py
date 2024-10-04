
import os
import pandas
import streamlit

from lib.generic import TESTBED_RATES
from lib.generic import LIMIT

from lib.generic import __variable_trend
from lib.generic import __cumulative_function

# DAZN Section #3
# This page contains the view-port on compiled Tstat traces, allowing the 
# user to explore which TCP and UDP flows occurred while streaming data.
# It lets the user appreciate more detailed statistics when streaming 
# linear content over DAZN.

SERVER = "dazn"

@streamlit.cache_data(show_spinner=True, ttl=10_000)
def load_samples(server: str, step: str, proto: str):
    medias = dict()

    for i, rate in enumerate(TESTBED_RATES):
        # generate the path
        cond = f"{rate}kbits" if rate != 'infi' else "infikbits"
        path = os.path.join(server, cond, "medias", proto, step)

        samples = []
        for dir in os.listdir(path):
            frame = pandas.read_csv(os.path.join(path, dir), sep=" ")
            samples.append(frame)
        samples = samples[:LIMIT]

        # save the samples
        medias[rate] = pandas.concat(samples, ignore_index=True)

    return medias
    
def variable_timeline_plot(y: str,
                           xaxis_title: str,
                           yaxis_title: str, 
                           chart_title: str, data: dict, y_log=False):
    x = "ts"
    __variable_trend(x=x, y=y,
                     data=data, 
                     xaxis_title=xaxis_title, 
                     yaxis_title=yaxis_title, chart_title=chart_title, y_log=True)

def tcp_section(data: dict):
    streamlit.caption("## Streaming over TCP")
    server, client = streamlit.columns(2)
    with server:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "bytes [B]"
        chart_title = "server bytes in tcp over time"
        y = "s_tcp_bytes"
        variable_timeline_plot(y=y,
                               xaxis_title=xaxis_title,
                               yaxis_title=yaxis_title,
                               chart_title=chart_title, data=data, y_log=True)

        xaxis_title = "bytes [B]"
        yaxis_title = "probability"
        chart_title = "cdf of server tcp bytes"
        x = "s_tcp_bytes"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)

    with client:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "bytes [B]"
        chart_title = "client bytes in tcp over time"
        y = "c_tcp_bytes"
        variable_timeline_plot(y=y,
                               xaxis_title=xaxis_title,
                               yaxis_title=yaxis_title,
                               chart_title=chart_title, data=data, y_log=True)
        
        xaxis_title = "bytes [B]"
        yaxis_title = "probability"
        chart_title = "cdf of client tcp bytes"
        x = "c_tcp_bytes"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)

    video, audio = streamlit.columns(2)
    with video:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "rate [kbits]"
        chart_title = "video quality"
        y = "avg_video_rate"
        variable_timeline_plot(y=y,
                               xaxis_title=xaxis_title,
                               yaxis_title=yaxis_title,
                               chart_title=chart_title, data=data, y_log=False)
        
    with audio:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "rate [kbits]"
        chart_title = "video quality"
        y = "avg_audio_rate"
        variable_timeline_plot(y=y,
                               xaxis_title=xaxis_title,
                               yaxis_title=yaxis_title,
                               chart_title=chart_title, data=data, y_log=False)
        
    col1, col2, col3, col4 = streamlit.columns(4)
    with col1:
        xaxis_title = "time [ms]"
        yaxis_title = "probability"
        chart_title = "cdf of average bins span"
        x = "avg_bins_span"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
    with col2:
        xaxis_title = "time [ms]"
        yaxis_title = "probability"
        chart_title = "cdf of standard deviation bins span"
        x = "std_bins_span"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
    with col3:
        xaxis_title = "time [ms]"
        yaxis_title = "probability"
        chart_title = "cdf of maximum bins span"
        x = "max_bins_span"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
    with col4:
        xaxis_title = "time [ms]"
        yaxis_title = "probability"
        chart_title = "cdf of minimum bins span"
        x = "min_bins_span"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
        
def udp_section(data: dict):
    streamlit.caption("## Streaming over UDP")
    server, client = streamlit.columns(2)
    with server:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "bytes [B]"
        chart_title = "server bytes in udp over time"
        y = "s_udp_bytes"
        variable_timeline_plot(y=y,
                               xaxis_title=xaxis_title,
                               yaxis_title=yaxis_title,
                               chart_title=chart_title, data=data, y_log=True)

        xaxis_title = "bytes [B]"
        yaxis_title = "probability"
        chart_title = "cdf of server udp bytes"
        x = "s_udp_bytes"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)

    with client:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "bytes [B]"
        chart_title = "client bytes in udp over time"
        y = "c_udp_bytes"
        variable_timeline_plot(y=y,
                               xaxis_title=xaxis_title,
                               yaxis_title=yaxis_title,
                               chart_title=chart_title, data=data, y_log=True)
        
        xaxis_title = "bytes [B]"
        yaxis_title = "probability"
        chart_title = "cdf of client udp bytes"
        x = "c_udp_bytes"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)

    video, audio = streamlit.columns(2)
    with video:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "rate [kbits]"
        chart_title = "video quality"
        y = "avg_video_rate"
        variable_timeline_plot(y=y,
                               xaxis_title=xaxis_title,
                               yaxis_title=yaxis_title,
                               chart_title=chart_title, data=data, y_log=False)
        
    with audio:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "rate [kbits]"
        chart_title = "audio quality"
        y = "avg_audio_rate"
        variable_timeline_plot(y=y,
                               xaxis_title=xaxis_title,
                               yaxis_title=yaxis_title,
                               chart_title=chart_title, data=data, y_log=False)
        
    col1, col2, col3, col4 = streamlit.columns(4)
    with col1:
        xaxis_title = "time [ms]"
        yaxis_title = "probability"
        chart_title = "cdf of average bins span"
        x = "avg_bins_span"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
    with col2:
        xaxis_title = "time [ms]"
        yaxis_title = "probability"
        chart_title = "cdf of standard deviation bins span"
        x = "std_bins_span"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
    with col3:
        xaxis_title = "time [ms]"
        yaxis_title = "probability"
        chart_title = "cdf of maximum bins span"
        x = "max_bins_span"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
    with col4:
        xaxis_title = "time [ms]"
        yaxis_title = "probability"
        chart_title = "cdf of minimum bins span"
        x = "min_bins_span"    
        __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)



def time_section():
    streamlit.caption("## Timings")

def __render():
    streamlit.markdown("---")

    tcp_samples = load_samples(server=SERVER, step="2000", proto="tcp")
    udp_samples = load_samples(server=SERVER, step="2000", proto="udp")

    tcp_section(data=tcp_samples)
    udp_section(data=udp_samples)
    time_section()