import enum
import pandas
import streamlit
import plotly.express as px
import plotly.graph_objects as go
import numpy


TEMPLATE = None
OPACITY  = 1.0
LIMIT    = 30

# enum for different log document types
class Document(enum.Enum):
    LOG_TCP_COMPLETE = 1
    LOG_TCP_PERIODIC = 2
    LOG_UDP_COMPLETE = 3
    LOG_UDP_PERIODIC = 4
    LOG_HAR_COMPLETE = 5
    LOG_STM_COMPLETE = 6
    LOG_VIDEO_COMPLETE = 7
    LOG_AUDIO_COMPLETE = 8

# enum for different protocols
class Protocol(enum.Enum):
    TCP  = 1
    UDP  = 2
    HTTP = 3

# log identifiers
LOG_TCP_COMPLETE = "log_tcp_complete"
LOG_TCP_PERIODIC = "log_tcp_periodic"
LOG_UDP_COMPLETE = "log_udp_complete"
LOG_UDP_PERIODIC = "log_udp_periodic"
LOG_BOT_COMPLETE = "log_bot_complete"
LOG_HAR_COMPLETE = "log_har_complete"
LOG_AUDIO_COMPLETE = "log_audio_complete"
LOG_VIDEO_COMPLETE = "log_video_complete"

# restbed bitrate conditions
TESTBED_RATES = [1500, 3000, 4500, 6000, 7500, 'infi']

# colors associated with testbed rates
TESTBED_RATES_COLORS = [
    '#8B0000',   # dark red
    '#FF0000',   # red
    '#FF4500',   # orange red
    '#FF7F00',   # orange
    '#FFFF00',   # yellow
    '#00FF00'    # green
]

# testbed birate conditions
TESTBED_RATES = [1500, 3000, 4500, 6000, 7500, 'infi']

# colors associated to testbed
TESTBED_RATES_COLORS = [
   '#8B0000',   # dark Red
    '#FF0000',  # red
    '#FF4500',  # orange Red
    '#FF7F00',  # orange
    '#FFFF00',  # yellow
    '#00FF00'   # green
]


def fmt_bitrate(bitrate: float) -> str:
    units = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']
    thresholds = [1, 1e3, 1e6, 1e9, 1e12]
    
    for i in range(len(thresholds) - 1, -1, -1):
        if bitrate >= thresholds[i]:
            value = bitrate / thresholds[i]
            return f"{value:.2f} {units[i]}"
    return "0 bps"

def fmt_volume(volume: int):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if volume < 1024:
            return f"{volume:2.2f} {unit}"
        volume /= 1024

def fmt_timestamp(timestamp: float):
    return f"{timestamp // 1000:.2f}s {timestamp % 1000:.2f}ms"

def timeline_axis(min_value, max_value):
    values = pandas.date_range(start=min_value, end=max_value, freq="10s")
    labels = [v.strftime("%M:%S") for v in values]
    return values, labels


def __layer4_timeline_info(record: dict, protocol: Protocol, document: Document) -> str:
    text = ""

    if protocol == Protocol.TCP:
        # format text for tcp timeline information
        text += (
            f"<b>CNAME</b> <br> {record['cname']} (TCP)<br>"
            f"<br>"
            f"<b>packets (client/server)</b><br>"
            f"  <b>pkts (data)</b> {record['c_pkts_data']} / {record['s_pkts_data']}<br>"
            f"  <b>ack pkts (pure)</b> {record['c_ack_cnt_p']} / {record['s_ack_cnt_p']}<br>"
            f"  <b>ack pkts (data)</b> {record['c_ack_cnt']} / {record['s_ack_cnt']}<br>"
            f"  <b>xmit  pkts</b> {record['c_pkts_all']} / {record['s_pkts_all']}<br>"
            f"  <b>rxmit pkts</b> {record['c_pkts_retx']} / {record['s_pkts_retx']}<br>"
            f"<br>"
            f"<b>bytes (client/server)</b><br>"
            f"  <b>bytes</b> {fmt_volume(record['c_bytes_all'])} / {fmt_volume(record['s_bytes_all'])}<br>"
            f"<br>"
            f"<b>timings</b><br>"
            f"<b>ts</b>  {fmt_timestamp(record['ts'])}<br>"
            f"<b>te</b>  {fmt_timestamp(record['te'])}<br>")

        if document == Document.LOG_TCP_COMPLETE:
            # add additional details for complete log
            text += (
                f"<b>first pkt with data (client)</b>  {fmt_timestamp(record['ts'] + record['c_first'])}<br>"
                f"<b>first pkt with data (server)</b>  {fmt_timestamp(record['ts'] + record['s_first'])}<br>")
            
        if document in {Document.LOG_TCP_PERIODIC, Document.LOG_UDP_PERIODIC}:
            text += f"<b>gp</b>  {fmt_timestamp(record['gap'])}<br>"

    if protocol == Protocol.UDP:
        # format text for udp timeline information
        text += (
            f"<b>CNAME</b> <br> {record['cname']} (UDP)<br>"
            f"<br>"
            f"<b>packets (client/server)</b><br>"
            f"  <b>pkts</b> {record['c_pkts_all']} / {record['s_pkts_all']}<br>"
            f"<br>"
            f"<b>bytes (client/server)</b><br>"
            f"  <b>bytes</b> {fmt_volume(record['c_bytes_all'])} / {fmt_volume(record['s_bytes_all'])}<br>"
            f"<br>"
            f"<b>timings</b><br>"
            f"<b>ts</b>  {fmt_timestamp(record['ts'])}<br>"
            f"<b>te</b>  {fmt_timestamp(record['te'])}<br>"
            f"<br>")
    
    return text

def __layer7_timeline_info(record: dict) -> str:
    return (
        f"<b>transaction</b> <br> {record['method']} {record['url']}<br>"
        f"<br>"
        f"<b>ts</b> {fmt_timestamp(record['ts'])}<br>"
        f"<b>te</b> {fmt_timestamp(record['te'])}<br>"
        f"<b>connection</b> {record['connection']}<br>")


def __timeline(data: pandas.DataFrame | None, 
               meta: pandas.DataFrame | None, 
               xs: str, 
               xe: str, y: str, 
               color: str,
               xaxis_title: str,
               yaxis_title: str,
               chart_title: str, info: str | None, legend=True, theme=None, log_scale=None):
    
    # generate a timeline figure
    fig = px.timeline(data_frame=data, 
                      x_start=xs, 
                      x_end=xe, 
                      y=y, 
                      color=color, 
                      custom_data=[info] if info else None, 
                      template=TEMPLATE)

    # add hover description
    if info:
        fig.update_traces(hovertemplate="%{customdata[0]}")

    # configure x-axis
    if meta is not None:
        values, labels = timeline_axis(min_value=pandas.Timestamp('1970-01-01 00:00:00'),
                                       max_value=pandas.to_datetime(meta["rel"].max(), unit="ms", origin="unix"))
    else:
        values, labels = timeline_axis(min_value=data[xs].min(), max_value=data[xe].max())
        
    # adjust height based on unique y-axis values
    height = 300 if len(data[y].unique()) < 10 else 500
    fig.update_layout(height=height)

    # set x and y axes
    fig.update_xaxes(tickvals=values, 
                     ticktext=labels, 
                     tickfont=dict(size=12), 
                     title=xaxis_title, 
                     showgrid=True)
    fig.update_yaxes(tickfont=dict(size=12), title=yaxis_title, showgrid=True)

    # set trace opacity and title
    fig.update_traces(opacity=OPACITY)
    fig.update_layout(title=chart_title, title_font=dict(size=12), showlegend=legend)

    # show the plot if no metadata
    if meta is None:
        streamlit.plotly_chart(fig, theme=theme, use_container_width=True)

    # add metadata plot rectangles
    if meta is not None:
        for i in range(0, len(meta) - 1, 2):
            x0, x1 = pandas.to_datetime(meta.loc[i:i+1, "rel"], unit="ms", origin="unix")
            name = meta.at[i, "event"]
            fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(255,255,0,0.1)", 
                          annotation_text=name, 
                          line_width=0, 
                          annotation_position="bottom right")

    # show the plot
    streamlit.plotly_chart(fig, theme=theme, use_container_width=True)


def __mean_variable_trend(media: pandas.DataFrame | None,
                          noise: pandas.DataFrame | None, 
                          x: str, 
                          y: str, 
                          xaxis_title: str,
                          yaxis_title: str,
                          chart_title: str, y_log=False):

    # helper function to add traces (common paradigm)
    def add_trace(frame: pandas.DataFrame, rate: str, i: int, mode: str, line_style: dict, marker_size=0):
        # process and aggregate data
        processed_data = (frame[frame[y] != 0]
                          .assign(**{x: frame[x] / 1000})
                          .groupby(x, as_index=False)[y].mean())

        # handle non-finite values by dropping them (NaN or inf)
        processed_data = processed_data.replace([numpy.inf, -numpy.inf], numpy.nan).dropna(subset=[y])

        # round y values to integers
        processed_data[y] = processed_data[y].round().astype(int)

        # convert x-axis to datetime format
        processed_data[x] = pandas.to_datetime(processed_data[x], origin="unix", unit='s')

        # add trace to the figure
        fig.add_trace(go.Scatter(
            x=processed_data[x], 
            y=processed_data[y], 
            mode=mode,
            marker=dict(color=TESTBED_RATES_COLORS[i], size=marker_size), 
            line=dict(color=TESTBED_RATES_COLORS[i], **line_style),
            name=f"{rate} kbits" if rate != 'infi' else "no-limits"))

    # create figure
    fig = go.Figure()

    # plot media traces
    for i, (rate, frame) in enumerate(media.items()):
        add_trace(frame, rate, i, 'lines+markers', {"width": 1}, marker_size=0.5)

    # plot noise traces if available
    if noise is not None:
        for i, (rate, frame) in enumerate(noise.items()):
            add_trace(frame, rate, i, 'lines', {"width": 0.5, "dash": "dot"}, marker_size=1)

    # configure axes and layout
    fig.update_xaxes(tickfont=dict(size=12), title=xaxis_title, showgrid=True, tickformat="%M:%S")
    fig.update_yaxes(tickfont=dict(size=12), title=yaxis_title, showgrid=True, type='log' if y_log else 'linear')
    fig.update_traces(opacity=OPACITY)
    fig.update_layout(title=chart_title, title_font=dict(size=12))

    # render plot in streamlit
    streamlit.plotly_chart(fig, use_container_width=True)




def __cumulative_function(x: str,
                          xaxis_title: str, 
                          yaxis_title: str,
                          chart_title: str, 
                          media: dict, noise: dict | None):

    # initialize a new figure
    fig = go.Figure()

    # helper function to add traces (common paradigm)
    def add_trace(frame: pandas.DataFrame, rate: str, i: int, mode: str, line_style: dict, marker_size=0):
        values = numpy.sort(frame[x])
        cumuls = numpy.arange(1, len(values) + 1) / len(values)
        fig.add_trace(go.Scatter(
            x=values, 
            y=cumuls,
            mode=mode,
            marker=dict(color=TESTBED_RATES_COLORS[i], size=marker_size), 
            line=dict(color=TESTBED_RATES_COLORS[i], **line_style),
            name=f"{rate} kbits" if rate != 'infi' else "no-limits"))

    # process media traces
    for i, (rate, frame) in enumerate(media.items()):
        add_trace(frame, rate, i, 'lines+markers', {"width": 1}, marker_size=0.5)

    # process noise traces, if any
    if noise is not None:
        for i, (rate, frame) in enumerate(noise.items()):
            add_trace(frame, rate, i, 'lines', {"width": 0.5, "dash": 'dash'}, marker_size=1)

    # update axes and layout
    fig.update_xaxes(title=xaxis_title, showgrid=True, type='log')
    fig.update_yaxes(title=yaxis_title, showgrid=True)
    fig.update_layout(title=chart_title, title_font=dict(size=12), 
                      showlegend=True, legend_title="testbed bitrate traces")

    streamlit.plotly_chart(fig, use_container_width=True)



def __scatter(x: str, 
              y: str, 
              xaxis_title: str, 
              yaxis_title: str, 
              chart_title: str, media: dict, noise: dict | None):
    
    # init a new figure
    fig = go.Figure()

    # add scatter plot for the main data
    for i, (rate, frame) in enumerate(media.items()):
        fig.add_trace(go.Scatter(
            x=frame[x], 
            y=frame[y],
            mode='markers',
            marker=dict(color=TESTBED_RATES_COLORS[i], size=5),
            name=f"{rate} kbits" if rate != 'infi' else "no-limits"))
        
    # # if noise data is provided, add scatter plot for the noise
    # if noise is not None:
    #     for i, (rate, frame) in enumerate(noise.items()):
    #         fig.add_trace(go.Scatter(
    #             x=frame[x],
    #             y=frame[y],
    #             mode='markers',
    #             marker=dict(color=TESTBED_RATES_COLORS[i], size=5, symbol='cross'),
    #             name=f"{rate} kbits (noise)" if rate != 'infi' else "no-limits (noise)"))

    # update axes and layout
    fig.update_xaxes(title=xaxis_title, showgrid=True)
    fig.update_traces(opacity=OPACITY)
    fig.update_yaxes(title=yaxis_title, showgrid=True)
    fig.update_layout(title=chart_title, title_font=dict(size=12),
                      showlegend=True, legend_title="testbed bitrate traces")

    # display the plot in Streamlit
    streamlit.plotly_chart(fig, use_container_width=True)



def __extract_streaming_periods(frame: pandas.DataFrame):

    frame = frame[~frame["event"].str.contains("sniffer|browser|origin|net|app", case=False, na=False)]
    frame = frame.reset_index(drop=True)

    return [(frame.loc[i, "rel"], frame.loc[i + 1, "rel"]) for i in range(0, len(frame) - 1, 2)]