
import os
import pandas
import numpy
import streamlit
import concurrent.futures

from lib.generic import TESTBED_RATES
from lib.generic import LIMIT

from lib.generic import Protocol

from lib.generic import __plot_scatter
from lib.generic import __plot_trend

# DAZN Section #3
# This page contains the view-port on compiled Tstat traces, allowing the 
# user to explore which TCP and UDP flows occurred while streaming data.
# It lets the user appreciate more detailed statistics when streaming 
# linear content over DAZN.

SERVER = "dazn"

@streamlit.cache_data(show_spinner=True, ttl=10_000)
def load_samples(step: str, protocol: Protocol):

    samples = {}

    # Loop over all available rates
    for rate in TESTBED_RATES:
        root = os.path.join(SERVER, rate, "media", "tcp" if protocol is Protocol.TCP else "udp", step)
        data = []

        # Loop over all files in the root directory
        for file in os.listdir(root):
            path = os.path.join(root, file)
            data.append(pandas.read_csv(path, sep=" "))

        # Generate a frame from data (only first 10 files)
        frame = pandas.concat(data[:25], ignore_index=True)

        x = "ts"  # Timestamp column

        # Group by 'ts' and calculate aggregates (ignoring 0 values)
        data = (frame[frame[x] != 0]
                .assign(**{x: frame[x] / 1000})  # Convert 'ts' from ms to seconds
                .groupby(x, as_index=False)
                .agg(
                    audio_reqs=("audio_reqs", lambda x: x[x != 0].mean()),  # Mean ignoring 0 values
                    video_reqs=("video_reqs", lambda x: x[x != 0].mean()),  # Mean ignoring 0 values
                    audio_rate=("avg_audio_rate", lambda x: x[x != 0].mean()),  # Mean ignoring 0 values
                    video_rate=("avg_video_rate", lambda x: x[x != 0].mean()),  # Mean ignoring 0 values
                    c_bytes_all=("c_bytes_all", "mean"),  # Mean of client bytes (no filtering)
                    s_bytes_all=("s_bytes_all", "mean"),  # Mean of server bytes (no filtering)
                    c_packs_all=("c_pkts_all", "mean"),   # Mean of client bytes (no filtering)
                    s_packs_all=("s_pkts_all", "mean"),   # Mean of server bytes (no filtering)
                    avg_bin_duration=("avg_bin_duration", "mean"),   # Mean of client bytes (no filtering)
                    max_bin_duration=("max_bin_duration", "mean"),   # Mean of server bytes (no filtering)
                    min_bin_duration=("min_bin_duration", "mean")    # Mean of server bytes (no filtering)
                ))

        # Replace timestamps with datetime format
        data[x] = pandas.to_datetime(data[x], origin="unix", unit='s')

        # Remove non-finite values (NaN, inf)
        data = data.replace([numpy.inf, -numpy.inf], numpy.nan).dropna()

        # Save the processed data for this rate
        samples[rate] = data

    return samples


def plot_protocol(protocol: Protocol, samples: dict):

    protocol = "TCP" if protocol is Protocol.TCP else "UDP"
    streamlit.caption(f"### {protocol}")

    server, client = streamlit.columns(2)
    with server:
        __plot_trend(x="ts", y="s_bytes_all", 
                   xaxis_title="time [mm:ss]", 
                   yaxis_title="bytes [B]", 
                   chart_title="server bytes over time", samples=samples)
    with client:
        __plot_trend(x="ts", y="c_bytes_all", 
                   xaxis_title="time [mm:ss]", 
                   yaxis_title="bytes [B]", 
                   chart_title="client bytes over time", samples=samples)
    video, audio = streamlit.columns(2)
    with video:
        __plot_trend(x="ts", y="video_rate", 
                   xaxis_title="time [mm:ss]", 
                   yaxis_title="rate [kbits]", 
                   chart_title="video quality over time", samples=samples)
        __plot_scatter(x="s_bytes_all", y="video_rate", 
                     xaxis_title="bytes [B]",
                     yaxis_title="rate [kbits]", 
                     chart_title="server bytes vs video rate", samples=samples)
        __plot_scatter(x="avg_bin_duration", y="video_rate", 
                     xaxis_title="bytes [B]",
                     yaxis_title="rate [kbits]", 
                     chart_title="server bytes vs audio rate", samples=samples)
    with audio:
        __plot_trend(x="ts", y="audio_rate", 
                   xaxis_title="time [mm:ss]", 
                   yaxis_title="rate [kbits]", 
                   chart_title="audio quality over time", samples=samples)
        __plot_scatter(x="s_bytes_all", y="audio_rate", 
                     xaxis_title="bytes [B]",
                     yaxis_title="rate [kbits]", 
                     chart_title="server bytes vs audio rate", samples=samples)
        __plot_scatter(x="avg_bin_duration", y="audio_rate", 
                     xaxis_title="bytes [B]",
                     yaxis_title="rate [kbits]", 
                     chart_title="server bytes vs audio rate", samples=samples)


def main():

    samples = load_samples(step="5000", protocol=Protocol.TCP)
    plot_protocol(protocol=Protocol.TCP, samples=samples)

    samples = load_samples(step="5000", protocol=Protocol.UDP)
    plot_protocol(protocol=Protocol.UDP, samples=samples)




def __render():

    samples = load_samples(step="5000", protocol=Protocol.TCP)
    plot_protocol(protocol=Protocol.TCP, samples=samples)

    samples = load_samples(step="5000", protocol=Protocol.UDP)
    plot_protocol(protocol=Protocol.UDP, samples=samples)
