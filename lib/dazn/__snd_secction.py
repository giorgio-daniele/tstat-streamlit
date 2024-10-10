import os
import pandas
import streamlit
import plotly.express as px

from lib.generic import OPACITY

SERVER = "dazn"

# file paths for the TCP and UDP CNAME data
tcp_file_path = "res/dazn/cnames_tcp.txt"
udp_file_path = "res/dazn/cnames_udp.txt"
nsamples_file_path = "res/dazn/num_samples.txt"
tsamples_file_path = "res/dazn/num_tcp_flows.txt"
usmplaes_file_path = "res/dazn/num_udp_flows.txt"

def load_cname_data(path: str):
    df = pandas.read_csv(path, sep=" ")
    return df

def load_sample_count(path: str) -> int:
    with open(path, 'r') as file:
        return int(file.read().strip())
    
def create_briefing():
    # Load sample counts
    num_samples = load_sample_count(path=nsamples_file_path)
    tcp_samples = load_sample_count(path=tsamples_file_path)
    udp_samples = load_sample_count(path=usmplaes_file_path)

    # Create a dictionary with the sample counts
    data = {
        "Number of Streaming Intervals Analyzed": [num_samples],
        "TCP Analyzed Flows": [tcp_samples],
        "UDP Analyzed Flows": [udp_samples]
    }

    streamlit.caption("### Dataset")
    frame = pandas.DataFrame(data)
    streamlit.dataframe(frame, use_container_width=True, hide_index=True)

    streamlit.caption("### Linear CNAMEs over TCP")
    data = {
        "Linear HTTP servers over TCP patterns": [
            "*livedazn.daznedge.net",
            "*livedazn.akamaized.net",
            "*live.cdn.indazn.com",
            "*live-dazn-cdn.dazn.com"
        ],
        "CDN": [
            "on-premise", 
            "akamai",
            "amazon cloudfront",
            "fastly"],
        "Regular expressions":  [
            "live*\.*.*daznedge\.net\b",
            "live*\.*.*akamaized\.net\b",
            "live*\.*.*dazn\.com\b",
            "live*\.*.*dazn\.com\b"],
    }

    frame = pandas.DataFrame(data)
    streamlit.dataframe(frame, use_container_width=True, hide_index=True)

    streamlit.caption("### Linear CNAMEs over UDP")
    data = {
        "Linear HTTP servers over UDP patterns": [
            "*livedazn.akamaized.net",
            "*live.cdn.indazn.com",
            "*live-dazn-cdn.dazn.com"
        ],
        "CDN": [
            "akamai",
            "amazon cloudfront",
            "fastly"],
        "Regular expressions":  [
            "live*\.*.*akamaized\.net\b",
            "live*\.*.*dazn\.com\b",
            "live*\.*.*dazn\.com\b"],
    }

    frame = pandas.DataFrame(data)
    streamlit.dataframe(frame, use_container_width=True, hide_index=True)

def __render():

    streamlit.html(os.path.join("www", SERVER, "__snd_section", "0.html"))

    # load data from files
    tcp_data = load_cname_data(tcp_file_path)
    udp_data = load_cname_data(udp_file_path)

    num_samples = load_sample_count(path=nsamples_file_path)
    tcp_samples = load_sample_count(path=tsamples_file_path)
    udp_samples = load_sample_count(path=usmplaes_file_path)

    # calculate probabilities as percentages
    tcp_data["probability"] = (tcp_data["abs"] / num_samples) * 100
    udp_data["probability"] = (udp_data["abs"] / num_samples) * 100  

    tcp, udp = streamlit.columns(2)
    with tcp:
        fig = px.bar(tcp_data, x='cname', y='probability')
        fig.update_layout(xaxis_tickangle=-90, yaxis_title='frequency [%]')
        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)
        fig.update_layout(xaxis_tickangle=-90)
        fig.update_traces(opacity=OPACITY)
        streamlit.plotly_chart(fig, use_container_width=True)

    with udp:
        fig = px.bar(udp_data, x='cname', y='probability')
        fig.update_layout(xaxis_tickangle=-90, yaxis_title='frequency [%]')
        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)
        fig.update_layout(xaxis_tickangle=-90)
        fig.update_traces(opacity=OPACITY)
        streamlit.plotly_chart(fig, use_container_width=True)
    create_briefing()
    streamlit.markdown("---")