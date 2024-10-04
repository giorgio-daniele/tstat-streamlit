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

from lib.generic import __tcp_udp_timeline_info
from lib.generic import __http_timeline_info
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


def print_layer7_section(data: pandas.DataFrame, meta: pandas.DataFrame):
    xs, xe = "datetime_ts", "datetime_te"

    # filter data based on keywords in the 'mime' column
    data = data[data["mime"].str.contains(r"audio|video|dash", na=False)]

    if data.empty:
        return
    
    __timeline(data=data, 
               meta=meta, 
               xs=xs, 
               xe=xe, y="mime", color="mime", 
               xaxis_title="time",
               yaxis_title="mime", 
               chart_title="resources requested", info="info", legend=True, theme="streamlit")
    

def __render():
    streamlit.markdown("---")
    
    def get_number(name: str):
        return int(name.split("-")[1]) if "-" in name else 0

    def load_data(file_path: str):
        return pandas.read_csv(file_path, sep=" ") if os.path.exists(file_path) else None

    def process_tcp_logs(file_path_complete: str, file_path_periodic: str):
        global tcp_complete, tcp_periodic
        tcp_complete = load_data(file_path_complete)
        if tcp_complete is not None:
            format_layer(data=tcp_complete, protocol=Protocol.TCP, document=Document.LOG_TCP_COMPLETE)

        tcp_periodic = load_data(file_path_periodic)
        if tcp_periodic is not None and tcp_periodic["c_pkts_data"].any():
            tcp_periodic = tcp_periodic[tcp_periodic["c_pkts_data"] > 0]
            format_layer(data=tcp_periodic, protocol=Protocol.TCP, document=Document.LOG_TCP_PERIODIC)

    def process_udp_logs(file_path_complete: str, file_path_periodic: str):
        global udp_complete, udp_periodic
        udp_complete = load_data(file_path_complete)
        if udp_complete is not None:
            format_layer(data=udp_complete, protocol=Protocol.UDP, document=Document.LOG_UDP_COMPLETE)

        udp_periodic = load_data(file_path_periodic)
        if udp_periodic is not None:
            format_layer(data=udp_periodic, protocol=Protocol.UDP, document=Document.LOG_UDP_PERIODIC)

    col1, col2 = streamlit.columns(2)

    with col1:
        qos = streamlit.selectbox("choose testbed bandwidth", os.listdir(SERVER))

    with col2:
        opts = [opt for opt in os.listdir(os.path.join(SERVER, qos)) if opt.startswith("test")]
        numb = streamlit.selectbox("choose test", sorted(opts, key=get_number))

    meta = None
    
    # Load logs
    bot_complete_file_path = os.path.join(SERVER, qos, numb, LOG_BOT_COMPLETE)
    bot_complete = load_data(bot_complete_file_path)
    if bot_complete is not None:
        key = "sniffer|browser|origin|net|app"
        meta = bot_complete[~bot_complete["event"].str.contains(key, case=False, na=False)].reset_index(drop=True)

    process_tcp_logs(
        os.path.join(SERVER, qos, numb, LOG_TCP_COMPLETE),
        os.path.join(SERVER, qos, numb, LOG_TCP_PERIODIC))

    process_udp_logs(
        os.path.join(SERVER, qos, numb, LOG_UDP_COMPLETE),
        os.path.join(SERVER, qos, numb, LOG_UDP_PERIODIC))

    har_complete_file_path = os.path.join(SERVER, qos, numb, LOG_HAR_COMPLETE)
    har_complete = load_data(har_complete_file_path)

    # tcp section
    streamlit.caption("### tstat tcp assembled flows")
    tcp_tokens = streamlit.multiselect("select tcp cnames", set(tcp_complete["cname"]))

    if tcp_tokens:
        for log_data, doc in [(tcp_complete, Document.LOG_TCP_COMPLETE), (tcp_periodic, Document.LOG_TCP_PERIODIC)]:
            print_layer4_section(data=log_data, meta=meta, protocol=Protocol.TCP, document=doc, cnames=tcp_tokens)
    else:
        streamlit.warning("you do not have selected any cname, nothing to see here")

    # udp section
    streamlit.caption("### tstat udp assembled flows")
    udp_tokens = streamlit.multiselect("select udp cnames", set(udp_complete["cname"]))

    if udp_tokens:
        for log_data, doc in [(udp_complete, Document.LOG_UDP_COMPLETE), (udp_periodic, Document.LOG_UDP_PERIODIC)]:
            print_layer4_section(data=log_data, meta=meta, protocol=Protocol.UDP, document=doc, cnames=udp_tokens)
    else:
        streamlit.warning("you do not have selected any cname, nothing to see here")

    # http section
    streamlit.caption("### http transactions archive")
    if har_complete is not None:
        format_layer(data=har_complete, protocol=Protocol.HTTP, document=Document.LOG_HAR_COMPLETE)
        print_layer7_section(data=har_complete, meta=meta)
