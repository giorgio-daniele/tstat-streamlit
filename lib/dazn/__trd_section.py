
import os
import pandas
import numpy
import streamlit

from lib.generic import TESTBED_RATES
from lib.generic import LIMIT

from lib.generic import __mean_variable_trend
from lib.generic import __cumulative_function

# DAZN Section #3
# This page contains the view-port on compiled Tstat traces, allowing the 
# user to explore which TCP and UDP flows occurred while streaming data.
# It lets the user appreciate more detailed statistics when streaming 
# linear content over DAZN.

SERVER = "dazn"

@streamlit.cache_data(show_spinner=True, ttl=10_000)
def load_samples(step: str, proto: str, media: bool):
    medias = dict()

    for i, rate in enumerate(TESTBED_RATES):
        # generate the path
        cond = f"{rate}kbits" if rate != 'infi' else "infikbits"
        path = os.path.join(SERVER, cond, "media" if media else "noise", proto, step)

        samples = []
        for dir in os.listdir(path):
            frame = pandas.read_csv(os.path.join(path, dir), sep=" ")
            samples.append(frame)
        samples = samples[:LIMIT]

        # save the samples
        medias[rate] = pandas.concat(samples, ignore_index=True)

    return medias
    
def variable_timeline_plot(media: pandas.DataFrame,
                           noise: pandas.DataFrame, y: str, 
                           xaxis_title: str,
                           yaxis_title: str,
                           chart_title: str, y_log=False):
    x = "ts"
    __mean_variable_trend(x=x, y=y,
                          media=media, noise=noise, 
                          xaxis_title=xaxis_title, 
                          yaxis_title=yaxis_title, 
                          chart_title=chart_title, y_log=y_log)

def protocol_section(media: dict, noise: dict, protocol: str):
    protocol_upper = protocol.upper()
    
    streamlit.caption(f"## Visualizzazioni in {protocol_upper}")

    # define column names dynamically based on the protocol
    server_bytes = f"s_{protocol}_bytes"
    client_bytes = f"c_{protocol}_bytes"

    server, client = streamlit.columns(2)
    
    # server-side plots
    with server:
        
        variable_timeline_plot(
            y=server_bytes,
            xaxis_title="time",
            yaxis_title="bytes [B]",
            chart_title=f"server bytes in {protocol_upper} over time",
            media=media, noise=noise, y_log=True)
        
        streamlit.markdown(f"""
            <div style="text-align: justify;font-size: 12px;">
                Le curve disegnate in continuo rappresentano
                l'evoluzione della grandezza <code>s_{protocol}_bytes</code>
                dei flussi operanti in {protocol_upper} e associati a
                server DASH; le curve disegnate tratteggiate
                rappresentano, invece, l'evoluzione dei byte
                inviati da tutti i server associati a servizi
                secondari e/o terziari, sempre in {protocol_upper}.
            </div""", unsafe_allow_html=True)

        __cumulative_function(
            x=server_bytes, 
            xaxis_title="bytes [B]", 
            yaxis_title="probability", 
            chart_title=f"CDF of server {protocol_upper} bytes", 
            data=media, noise=noise)        

    # client-side plots
    with client:

        variable_timeline_plot(
            y=client_bytes,
            xaxis_title="time",
            yaxis_title="bytes [B]",
            chart_title=f"client bytes in {protocol_upper} over time",
            media=media, noise=noise, y_log=True)
        
        streamlit.markdown(f"""
            <div style="text-align: justify;font-size: 12px;">
                Le curve disegnate in continuo rappresentano
                l'evoluzione della grandezza <code>c_{protocol}_bytes</code>
                dei flussi operanti in {protocol_upper} e associati a
                server DASH; le curve disegnate tratteggiate
                rappresentano, invece, l'evoluzione dei byte
                inviati da tutti i server associati a servizi
                secondari e/o terziari, sempre in {protocol_upper}.
            </div""", unsafe_allow_html=True)
        
        
        __cumulative_function(
            x=client_bytes, 
            xaxis_title="bytes [B]", 
            yaxis_title="probability", 
            chart_title=f"CDF of client {protocol_upper} bytes", 
            data=media, noise=noise)
    
    __cumulative_function(
            x="avg_bins_span", 
            xaxis_title="time [ms]", 
            yaxis_title="probability", 
            chart_title=f"CDF of average bins span in {protocol_upper}", 
            data=media, noise=noise)

    # video and audio plots
    video, audio = streamlit.columns(2)
    with video:

        variable_timeline_plot(
            y="avg_video_rate",
            xaxis_title="time",
            yaxis_title="rate [kbits]",
            chart_title="video quality",
            media=media, noise=None, y_log=True)
        
        streamlit.markdown(f"""
            <div style="text-align: justify;font-size: 12px;">
                Le curve rappresentate in figura rappresentano l'evolouzione
                della qualità del video riprodutto nel corso delle visualizzazioni
                avvenute in {protocol_upper}. Si noti chiaramente la distribuzione
                delle curve in funzione della qualità riprodotta e come le
                limitazione di larghezza di banda impattino negativamente. 
            </div""", unsafe_allow_html=True)
        
    with audio:
        variable_timeline_plot(
            y="avg_audio_rate",
            xaxis_title="time",
            yaxis_title="rate [kbits]",
            chart_title="audio quality",
            media=media, noise=None, y_log=True)
        
        streamlit.markdown(f"""
            <div style="text-align: justify;font-size: 12px;">
                Le curve rappresentate in figura rappresentano l'evolouzione
                della qualità del video riprodutto nel corso delle visualizzazioni
                avvenute in {protocol_upper}. Si noti chiaramente che nessuna
                condizione di larghezza di banda produce variazioni nella qualità
                dell'audio riprodotto.
            </div""", unsafe_allow_html=True)

        
    # col1, col2, col3, col4 = streamlit.columns(4)
    # with col1:
    #     xaxis_title = "time [ms]"
    #     yaxis_title = "probability"
    #     chart_title = "cdf of average bins span"
    #     x = "avg_bins_span"    
    #     __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
    # with col2:
    #     xaxis_title = "time [ms]"
    #     yaxis_title = "probability"
    #     chart_title = "cdf of standard deviation bins span"
    #     x = "std_bins_span"    
    #     __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
    # with col3:
    #     xaxis_title = "time [ms]"
    #     yaxis_title = "probability"
    #     chart_title = "cdf of maximum bins span"
    #     x = "max_bins_span"    
    #     __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)
    # with col4:
    #     xaxis_title = "time [ms]"
    #     yaxis_title = "probability"
    #     chart_title = "cdf of minimum bins span"
    #     x = "min_bins_span"    
    #     __cumulative_function(x=x, xaxis_title=xaxis_title, yaxis_title=yaxis_title, chart_title=chart_title, data=data)



def __render():
    streamlit.html(os.path.join("www", SERVER, "__trd_section", "0.html"))

    step = "10000"

    tcp_media = load_samples(step=step, proto="tcp", media=True)
    udp_media = load_samples(step=step, proto="udp", media=True)
    tcp_noise = load_samples(step=step, proto="tcp", media=False)
    udp_noise = load_samples(step=step, proto="udp", media=False)

    protocol_section(media=tcp_media, noise=tcp_noise, protocol="tcp")
    streamlit.markdown("---")
    protocol_section(media=udp_media, noise=udp_noise, protocol="udp")
    streamlit.markdown("---")
    #noise_section(media=all_samples_media, noise=all_samples_noise)