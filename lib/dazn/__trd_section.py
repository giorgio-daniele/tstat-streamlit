
import os
import pandas
import numpy
import streamlit
import concurrent.futures

from lib.generic import TESTBED_RATES
from lib.generic import LIMIT

from lib.generic import Protocol

from lib.generic import __mean_variable_trend
from lib.generic import __cumulative_function
from lib.generic import __scatter

# DAZN Section #3
# This page contains the view-port on compiled Tstat traces, allowing the 
# user to explore which TCP and UDP flows occurred while streaming data.
# It lets the user appreciate more detailed statistics when streaming 
# linear content over DAZN.

SERVER = "dazn"

def load_single_sample(path: str):
    return pandas.read_csv(path, sep=" ")

@streamlit.cache_data(show_spinner=True, ttl=10_000)
def load_samples(step: str, proto: Protocol, media: bool):

    data  = {}
    proto = "tcp" if proto == Protocol.TCP else "udp"

    for rate in TESTBED_RATES:
        cond = f"{rate}kbits" if rate != 'infi' else "infikbits"
        path = os.path.join(
            SERVER, 
            cond, 
            "media" if media else "noise", proto, step)
        
        paths = [os.path.join(path, f) for f in os.listdir(path)][:LIMIT]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            samples = list(executor.map(load_single_sample, paths))
        data[rate] = pandas.concat(samples, ignore_index=True)
    
    return data


def create_trend_charts(x: str, 
                        y: str, 
                        media: dict | None,
                        noise: dict | None,
                        xaxis_title: str, 
                        yaxis_title: str, 
                        chart_title: str, log_scale: bool = False):
    
    __mean_variable_trend(
        x=x, 
        y=y, 
        media=media, 
        noise=noise,
        xaxis_title=xaxis_title, 
        yaxis_title=yaxis_title,
        chart_title=chart_title, 
        y_log=log_scale)

def create_cdf_charts(x: str, 
                      media: dict, 
                      noise: dict, 
                      xaxis_title: str, 
                      yaxis_title: str, 
                      chart_title: str):
    
    __cumulative_function(
        x=x, 
        media=media, 
        noise=noise,
        xaxis_title=xaxis_title, 
        yaxis_title=yaxis_title,
        chart_title=chart_title)

def create_scatter_charts(x: str, 
                          y: str, 
                          media: dict, 
                          noise: dict, 
                          xaxis_title: str, 
                          yaxis_title: str, 
                          chart_title: str):
    
    __scatter(
        x=x, 
        y=y, 
        media=media, 
        noise=noise,
        xaxis_title=xaxis_title, 
        yaxis_title=yaxis_title,
        chart_title=chart_title)

    
def protocol_section(step: str, 
                     media: dict, 
                     noise: dict, protocol: Protocol):

    layer = ""
    if protocol is Protocol.TCP:
        layer = "TCP"
    if protocol is Protocol.UDP:
        layer = "UDP"

    streamlit.caption(f"# Livello {layer}")

    ##########################################################
    # HAR section
    ##########################################################
    streamlit.caption(f"## Analisi audio e video")
    video_reqs, audio_reqs, video_qoe, audio_qoe = streamlit.columns(4)
    with video_reqs:
        x, y = "ts", "num_vid"
        xaxis_title = "time [mm:ss]"
        yaxis_title = "requests [#]"
        chart_title = "Richieste video nel tempo"
        create_trend_charts(x=x, y=y,
            xaxis_title=xaxis_title, 
            yaxis_title=yaxis_title, 
            chart_title=chart_title, media=media, noise=None, log_scale=False)
    with audio_reqs:
        x, y = "ts", "num_aud"
        xaxis_title = "time [mm:ss]"
        yaxis_title = "requests [#]"
        chart_title = "Richieste audio nel tempo"
        create_trend_charts(x=x, y=y,
            xaxis_title=xaxis_title, 
            yaxis_title=yaxis_title, 
            chart_title=chart_title, media=media, noise=None, log_scale=False)
    with video_qoe:
        x, y = "ts", "avg_vid"
        xaxis_title = "time [mm:ss]"
        yaxis_title = "rate [kbits]"
        chart_title = "Qualità video nel tempo"
        create_trend_charts(x=x, y=y,
            xaxis_title=xaxis_title, 
            yaxis_title=yaxis_title, 
            chart_title=chart_title, media=media, noise=None, log_scale=False)
    with audio_qoe:
        x, y = "ts", "avg_aud"
        xaxis_title = "time [mm:ss]"
        yaxis_title = "rate [kbits]"
        chart_title = "Qualità audio nel tempo"
        create_trend_charts(x=x, y=y,
            xaxis_title=xaxis_title, 
            yaxis_title=yaxis_title, 
            chart_title=chart_title, media=media, noise=None, log_scale=False)


    ##########################################################
    # L4 section
    ##########################################################
    streamlit.caption(f"## Analisi volumetrica")
    server, client = streamlit.columns(2)

    with server:
        streamlit.caption(f"## Server")
        col1, col2 = streamlit.columns(2)
        with col1:
            x = "ts"
            y = "s_bytes_uniq" if protocol == Protocol.TCP else "s_bytes_all"
            xaxis_title = "time [mm:ss]"
            yaxis_title = "bytes [B]"
            chart_title = "Bytes inviati dal server nel tempo"
            create_trend_charts(x=x, y=y,
                xaxis_title=xaxis_title, 
                yaxis_title=yaxis_title, 
                chart_title=chart_title, media=media, noise=None, log_scale=True)
            # x = "ts"
            # y = "s_pkts_data" if protocol == Protocol.TCP else "s_pkts_all"
            # xaxis_title = "time [mm:ss]"
            # yaxis_title = "packets [#]"
            # chart_title = "Pacchetti inviati dal server nel tempo"
            # create_trend_charts(x=x, y=y,
            #     xaxis_title=xaxis_title, 
            #     yaxis_title=yaxis_title, 
            #     chart_title=chart_title, media=media, noise=None, log_scale=True)
                
        with col2:
            x = "s_bytes_uniq" if protocol == Protocol.TCP else "s_bytes_all"
            xaxis_title = "bytes [B]"
            yaxis_title = "probability [%]"
            chart_title = "Funzione di ripatizione su bytes trasmessi dal server"
            create_cdf_charts(x=x,
                media=media, noise=noise,
                xaxis_title=xaxis_title, 
                yaxis_title=yaxis_title, 
                chart_title=chart_title)
            # x = "s_pkts_data" if protocol == Protocol.TCP else "s_pkts_all"
            # xaxis_title = "packets [#]"
            # yaxis_title = "probability [%]"
            # chart_title = "Funzione di ripatizione su pacchetti trasmessi dal server"
            # create_cdf_charts(x=x,
            #     media=media, noise=noise,
            #     xaxis_title=xaxis_title, 
            #     yaxis_title=yaxis_title, 
            #     chart_title=chart_title)

    with client:
        streamlit.caption(f"## Client")
        col1, col2 = streamlit.columns(2)
        with col1:
            x = "ts"
            y = "c_bytes_uniq" if protocol == Protocol.TCP else "c_bytes_all"
            xaxis_title = "time [mm:ss]"
            yaxis_title = "bytes [B]"
            chart_title = "Bytes inviati dal client nel tempo"
            create_trend_charts(x=x, y=y,
                xaxis_title=xaxis_title, 
                yaxis_title=yaxis_title, 
                chart_title=chart_title, media=media, noise=None, log_scale=True)
            # x = "ts"
            # y = "c_pkts_data" if protocol == Protocol.TCP else "c_pkts_all"
            # xaxis_title = "time [mm:ss]"
            # yaxis_title = "packets [#]"
            # chart_title = "Pacchetti inviati dal client nel tempo"
            # create_trend_charts(x=x, y=y,
            #     xaxis_title=xaxis_title, 
            #     yaxis_title=yaxis_title, 
            #     chart_title=chart_title, media=media, noise=None, log_scale=True)
        with col2:
            x = "c_bytes_uniq" if protocol == Protocol.TCP else "c_bytes_all"
            xaxis_title = "bytes [B]"
            yaxis_title = "probability [%]"
            chart_title = "Funzione di ripatizione su bytes trasmessi dal client"
            create_cdf_charts(x=x,
                media=media, noise=noise,
                xaxis_title=xaxis_title, 
                yaxis_title=yaxis_title, 
                chart_title=chart_title)
            # x = "c_pkts_data" if protocol == Protocol.TCP else "c_pkts_all"
            # xaxis_title = "packets [#]"
            # yaxis_title = "probability [%]"
            # chart_title = "Funzione di ripatizione su pacchetti trasmessi dal client"
            # create_cdf_charts(x=x,
            #     media=media, noise=noise,
            #     xaxis_title=xaxis_title, 
            #     yaxis_title=yaxis_title, 
            #     chart_title=chart_title)

    ##########################################################
    # Time section
    ##########################################################
    streamlit.caption(f"## Analisi temporale")
    col1, col2 = streamlit.columns(2)
    with col1:
        x, y = "ts", "avg_bin"
        xaxis_title = "time [mm:ss]"
        yaxis_title = "time [ms]"
        chart_title = "Durata media dei bin nel tempo"
        create_trend_charts(x=x, y=y,
            xaxis_title=xaxis_title, 
            yaxis_title=yaxis_title, 
            chart_title=chart_title, media=media, noise=None, log_scale=False)
    with col2:
        x = "avg_bin"
        xaxis_title = "time [ms]"
        yaxis_title = "probability [%]"
        chart_title = "Funzione di ripatizione della durata media dei bin"
        create_cdf_charts(x=x,
                media=media, noise=None,
                xaxis_title=xaxis_title, 
                yaxis_title=yaxis_title, 
                chart_title=chart_title)

    ##########################################################
    # Correlation section
    ##########################################################
    streamlit.caption(f"## Analisi di correlazione")
    col1, col2 = streamlit.columns(2)
    with col1:
        x = "s_bytes_uniq" if protocol == Protocol.TCP else "s_bytes_all"
        y = "avg_vid"
        yaxis_title = "rate [kbits]"
        xaxis_title = "bytes [B]"
        chart_title = "Correlazione tra bytes inviati dal server e qualità video"
        create_scatter_charts(x=x, y=y,
                media=media, noise=None,
                xaxis_title=xaxis_title, 
                yaxis_title=yaxis_title, 
                chart_title=chart_title)
    with col2:
        x = "c_bytes_uniq" if protocol == Protocol.TCP else "c_bytes_all"
        y = "avg_vid"
        yaxis_title = "rate [kbits]"
        xaxis_title = "bytes [B]"
        chart_title = "Correlazione tra bytes inviati dal client e qualità video"
        create_scatter_charts(x=x, y=y,
                media=media, noise=None,
                xaxis_title=xaxis_title, 
                yaxis_title=yaxis_title, 
                chart_title=chart_title)




def __render():
    step = "5000"

    tcp_media = load_samples(step=step, proto=Protocol.TCP, media=True)
    udp_media = load_samples(step=step, proto=Protocol.UDP, media=True)
    tcp_noise = load_samples(step=step, proto=Protocol.TCP, media=False)
    udp_noise = load_samples(step=step, proto=Protocol.UDP, media=False)

    streamlit.html(os.path.join("www", SERVER, "__trd_section", "0.html"))

    protocol_section(
        step=str(int(step) // 1000), 
        media=tcp_media, 
        noise=tcp_noise, protocol=Protocol.TCP)
    
    streamlit.markdown("---")
    
    protocol_section(
        step=str(int(step) // 1000), 
        media=udp_media, 
        noise=udp_noise, protocol=Protocol.UDP)
