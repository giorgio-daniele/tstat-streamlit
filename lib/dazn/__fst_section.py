import os
import pandas
import streamlit

from lib.generic import Protocol
from lib.generic import Document

from lib.generic import LOG_BOT_COMPLETE
from lib.generic import LOG_HAR_COMPLETE
from lib.generic import LOG_TCP_COMPLETE
from lib.generic import LOG_UDP_COMPLETE
from lib.generic import LOG_TCP_PERIODIC
from lib.generic import LOG_UDP_PERIODIC

from lib.generic import LOG_AUDIO_COMPLETE
from lib.generic import LOG_VIDEO_COMPLETE

from lib.generic import __tcp_udp_timeline_info
from lib.generic import __http_timeline_info
from lib.generic import __variable_trend
from lib.generic import __timeline


# DAZN Section #1
# This page contains the view-port on compiled Tstat traces, allowing the 
# user to explore which TCP and UDP flows occurred while streaming data.

SERVER = "dazn"

def format_layer(data: pandas.DataFrame, protocol: Protocol, document: Document):

    ts, te = "ts", "te"
    data[f"datetime_{ts}"] = pandas.to_datetime(data[ts], unit="ms", origin="unix")
    data[f"datetime_{te}"] = pandas.to_datetime(data[te], unit="ms", origin="unix")

    if document in {Document.LOG_TCP_COMPLETE, Document.LOG_UDP_COMPLETE, Document.LOG_TCP_PERIODIC, Document.LOG_UDP_PERIODIC}:
        data["info"] = data.apply(lambda r: __tcp_udp_timeline_info(record=r, protocol=protocol, document=document), axis=1)
    elif document == Document.LOG_HAR_COMPLETE:
        data["info"] = data.apply(lambda r: __http_timeline_info(record=r), axis=1)
    elif document == Document.LOG_AUDIO_COMPLETE:
        data["info"] = data.apply(lambda r: __http_timeline_info(record=r), axis=1)
    elif document == Document.LOG_VIDEO_COMPLETE:
        data["info"] = data.apply(lambda r: __http_timeline_info(record=r), axis=1)


def print_layer4_section(data: pandas.DataFrame, 
                         meta: pandas.DataFrame, 
                         protocol: Protocol, 
                         document: Document, cnames: list[str]):
    
    xs, xe = "datetime_ts", "datetime_te"

    protocol_map = {Protocol.TCP: "tcp", Protocol.UDP: "udp"}
    document_map = {
        Document.LOG_TCP_COMPLETE: "complete", Document.LOG_UDP_COMPLETE: "complete",
        Document.LOG_TCP_PERIODIC: "periodic", Document.LOG_UDP_PERIODIC: "periodic"}

    chart_title = f"log_{protocol_map.get(protocol, '')}_{document_map.get(document, '')}"

    data = data[data["cname"].isin(cnames)]
    if data.empty:
        return

    data = data.sort_values(by="c_port", ascending=False)
    data["id"] = data.apply(lambda row: f"{row['c_ip']}:{row['c_port']}-{row['s_ip']}:{row['s_port']}", axis=1)

    __timeline(data=data, 
               meta=meta, 
               xs=xs, 
               xe=xe, y="id", color="cname", 
               xaxis_title="time [mm:ss]", 
               yaxis_title="flow", 
               chart_title=chart_title, info="info", legend=True, theme="streamlit")


def print_layer7_section(hcom: pandas.DataFrame,
                         meta: pandas.DataFrame, acom: pandas.DataFrame, vcom: pandas.DataFrame):
    
    xs, xe = "datetime_ts", "datetime_te"

    # filter data based on keywords in the 'mime' column
    data = hcom[hcom["mime"].str.contains(r"audio|video|dash", na=False)]

    if data.empty:
        return
    
    __timeline(data=data, 
               meta=meta, 
               xs=xs, 
               xe=xe, y="mime", color="mime", 
               xaxis_title="time",
               yaxis_title="mime", 
               chart_title="http transactions timeline", info="info", legend=True, theme="streamlit")
    

    col1, col2 = streamlit.columns(2)


    with col1:
        __variable_trend(data=vcom, meta=meta, xs=xs, xe=xe, y="size",
                        xaxis_title="time",
                        yaxis_title="bytes [B]",
                        chart_title="http video responses size over time",
                        y_log_scale=True, color="blue")
        
        __variable_trend(data=vcom, meta=meta, xs=xs, xe=xe, y="video_bitrate",
                        xaxis_title="time",
                        yaxis_title="rate [kbits]",
                        chart_title="http video bitrate over time",
                        y_log_scale=False, color="blue")
    
    with col2:
        __variable_trend(data=acom, meta=meta, xs=xs, xe=xe, y="size",
                        xaxis_title="time",
                        yaxis_title="bytes [B]",
                        chart_title="http audio responses size over time",
                        y_log_scale=False, color="red")
        
        __variable_trend(data=acom, meta=meta, xs=xs, xe=xe, y="audio_bitrate",
                        xaxis_title="time",
                        yaxis_title="rate [kbits]",
                        chart_title="http audio bitrate over time",
                        y_log_scale=False, color="red")
    
        
    
def get_number(name: str):
    return int(name.split("-")[1]) if "-" in name else 0

def load_data(path: str):
    return pandas.read_csv(path, sep=" ") if os.path.exists(path) else None

def process_tcp_logs(com: str, per: str):
    global tcom, tper

    tcom = load_data(path=com)
    if tcom is not None:
        format_layer(data=tcom, protocol=Protocol.TCP, document=Document.LOG_TCP_COMPLETE)

    tper = load_data(path=per)
    if tper is not None and tper["c_pkts_data"].any():
        tper = tper[tper["c_pkts_data"] > 0]
        format_layer(data=tper, protocol=Protocol.TCP, document=Document.LOG_TCP_PERIODIC)

def process_udp_logs(com: str, per: str):
    global ucom, uper

    ucom = load_data(path=com)
    if ucom is not None:
        format_layer(data=ucom, protocol=Protocol.UDP, document=Document.LOG_UDP_COMPLETE)

    uper = load_data(path=per)
    if uper is not None:
        format_layer(data=uper, protocol=Protocol.UDP, document=Document.LOG_UDP_PERIODIC)
    

def __render():
    streamlit.caption("# TCP, UDP, and HTTP flows")
    col1, col2 = streamlit.columns(2)

    with col1:
        qos = streamlit.selectbox("Choose testbed bandwidth", os.listdir(SERVER))

    with col2:
        opts = [opt for opt in os.listdir(os.path.join(SERVER, qos)) if opt.startswith("test")]
        numb = streamlit.selectbox("Choose supervised experiment", sorted(opts, key=get_number))

    meta = None
    
    # Load logs
    path = os.path.join(SERVER, qos, numb, LOG_BOT_COMPLETE)
    bcom = load_data(path=path)
    if bcom is not None:
        key = "sniffer|browser|origin|net|app"
        meta = bcom[~bcom["event"].str.contains(key, case=False, na=False)].reset_index(drop=True)

    process_tcp_logs(
        com=os.path.join(SERVER, qos, numb, LOG_TCP_COMPLETE),
        per=os.path.join(SERVER, qos, numb, LOG_TCP_PERIODIC))

    process_udp_logs(
        com=os.path.join(SERVER, qos, numb, LOG_UDP_COMPLETE),
        per=os.path.join(SERVER, qos, numb, LOG_UDP_PERIODIC))

    path = os.path.join(SERVER, qos, numb, LOG_HAR_COMPLETE)
    hcom = load_data(path=path)

    path = os.path.join(SERVER, qos, numb, LOG_VIDEO_COMPLETE)
    vcom = load_data(path=path)

    path = os.path.join(SERVER, qos, numb, LOG_AUDIO_COMPLETE)
    acom = load_data(path=path)

    # tcp section
    streamlit.caption("## TCP")
    tcp_tokens = streamlit.multiselect("Select CNAMES over TCP flows", set(tcom["cname"]))

    if tcp_tokens:
        for log_data, doc in [(tcom, Document.LOG_TCP_COMPLETE), (tper, Document.LOG_TCP_PERIODIC)]:
            print_layer4_section(data=log_data, meta=meta, protocol=Protocol.TCP, document=doc, cnames=tcp_tokens)
    else:
        streamlit.warning("You do not have selected any CNAME, nothing to see here")

    # udp section
    streamlit.caption("## UDP")
    udp_tokens = streamlit.multiselect("Select CNAMEs over UDP flows", set(ucom["cname"]))

    if udp_tokens:
        for log_data, doc in [(ucom, Document.LOG_UDP_COMPLETE), (uper, Document.LOG_UDP_PERIODIC)]:
            print_layer4_section(data=log_data, meta=meta, protocol=Protocol.UDP, document=doc, cnames=udp_tokens)
    else:
        streamlit.warning("You do not have selected any CNAME, nothing to see here")

    # http section
    streamlit.caption("## HTTP")
    if hcom is not None:
        format_layer(data=hcom, protocol=Protocol.HTTP, document=Document.LOG_HAR_COMPLETE)
        format_layer(data=vcom, protocol=Protocol.HTTP, document=Document.LOG_VIDEO_COMPLETE)
        format_layer(data=acom, protocol=Protocol.HTTP, document=Document.LOG_AUDIO_COMPLETE)
        print_layer7_section(hcom=hcom,  meta=meta,  vcom=vcom, acom=acom)
    streamlit.markdown("---")