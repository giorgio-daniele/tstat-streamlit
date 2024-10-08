import enum
import pandas
import streamlit
import plotly.express as px
import plotly.graph_objects as go
import numpy


TEMPLATE = None
OPACITY  = 1.0
LIMIT    = 15

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

def __tcp_udp_timeline_info(record: dict, protocol: Protocol, document: Document) -> str:
    text = ""

    if protocol == Protocol.TCP:
        # retrieve packet and byte counts for TCP
        c_packs = record["c_pkts_all"]  # client packets
        s_packs = record["s_pkts_all"]  # server packets
        c_bytes = record["c_bytes_all"]  # client bytes
        s_bytes = record["s_bytes_all"]  # server bytes
        c_packs_app = record["c_pkts_data"]  # client packets with layer7 data
        s_packs_app = record["s_pkts_data"]  # server packets with layer7 data
        c_packs_ack_pure = record["c_ack_cnt_p"]  # client pure ACKs
        s_packs_ack_pure = record["s_ack_cnt_p"]  # server pure ACKs
        c_packs_ack_data = record["c_ack_cnt"]  # client ACKs with data
        s_packs_ack_data = record["s_ack_cnt"]  # server ACKs with data
        c_packs_rxt = record["c_pkts_retx"]  # client retransmitted packets
        s_packs_rxt = record["s_pkts_retx"]  # server retransmitted packets

        # Format the text for TCP timeline information
        text += (
            f"<b>server name</b> <br> {record['cname']} <br>"
            f"<br>"
            f"<b>packs (client/server)</b><br>"
            f"  <b>app</b> {(c_packs_app)} / {(s_packs_app)}<br>"
            f"  <b>acks (pure)</b> {(c_packs_ack_pure)} / {(s_packs_ack_pure)}<br>"
            f"  <b>acks (data)</b> {(c_packs_ack_data)} / {(s_packs_ack_data)}<br>"
            f"  <b>all</b> {(c_packs)} / {(s_packs)}<br>"
            f"  <b>rxt</b> {(c_packs_rxt)} / {(s_packs_rxt)}<br>"
            f"<br>"
            f"<b>bytes (client/server)</b><br>"
            f"  <b>all</b> {fmt_volume(c_bytes)} / {fmt_volume(s_bytes)}<br>"
            f"<br>"
            f"<b>timings</b><br>"
            f"<b>ts</b>  {fmt_timestamp(record['ts'])}<br>"
            f"<b>te</b>  {fmt_timestamp(record['te'])}<br>"
            f"<b>lasting</b> {fmt_timestamp(record['te'] - record['ts'])}<br>"
        )

        if document == Document.LOG_TCP_COMPLETE:
            c_first = record["c_first"]
            s_first = record["s_first"]

            # add additional details for complete log
            text += (
                f"<b>first pack data (client)</b>  {fmt_timestamp(record['ts'] + c_first)}<br>"
                f"<b>first pack data (server)</b>  {fmt_timestamp(record['ts'] + s_first)}<br>"
                f"<b>handshake lasting</b>  {fmt_timestamp(record['c_first'])}<br>"
            )

    if protocol == Protocol.UDP:
        # retrieve packet and byte counts for UDP
        c_packs = record["c_pkts_all"]  # client packets
        s_packs = record["s_pkts_all"]  # server packets
        c_bytes = record["c_bytes_all"]  # client bytes
        s_bytes = record["s_bytes_all"]  # server bytes

        # format the text for UDP timeline information
        text += (
            f"<b>server name</b> <br> {record['cname']} <br>"
            f"<br>"
            f"<b>packs (client/server)</b><br>"
            f"  <b>all</b> {(c_packs)} / {(s_packs)}<br>"
            f"<br>"
            f"<b>bytes (client/server)</b><br>"
            f"  <b>all</b> {fmt_volume(c_bytes)} / {fmt_volume(s_bytes)}<br>"
            f"<br>"
            f"<b>timings</b><br>"
            f"<b>ts</b>  {fmt_timestamp(record['ts'])}<br>"
            f"<b>te</b>  {fmt_timestamp(record['ts'])}<br>"
            f"<br>"
        )
    
    return text

# function to extract HTTP timeline information from a record
def __http_timeline_info(record: dict) -> str:
    text = (
        f"<b>transaction</b> <br> {record['method']} {record['url']}<br>"
        f"<br>"
        f"<b>ts</b> {fmt_timestamp(record['ts'])}<br>"
        f"<b>te</b> {fmt_timestamp(record['te'])}<br>"
        f"<b>connection</b> {record['connection']}<br>"
    )
    return text


def __variable_trend(data: pandas.DataFrame,
                     meta: pandas.DataFrame, xs: str, xe: str, y: str,
                     xaxis_title: str,
                     yaxis_title: str,
                     chart_title: str, y_log_scale: bool, color: str):
    
    # |  xs  |  xe  |  var  |
    # |------|------|-------|
    # |  1   |  3   |  10   |
    # |  3   |  5   |  15   |
    # |  5   |  8   |  12   |
    # | ...  | .... | ..... |

    # generate a new figure
    fig = go.Figure()

    x_values = []
    y_values = []

    # loop over the variables
    for j, rec in data.iterrows():
        x_values.append(rec[xs])
        x_values.append(rec[xe])

        y_values.append(rec[y])
        y_values.append(rec[y])

    fig.add_trace(go.Scatter(
        x=x_values, 
        y=y_values, mode="markers+lines", 
            marker=dict(color=color, size=3), line=dict(color=color, width=0.5, dash='dash')))
            
    y_scale = "log" if y_log_scale else "linear"

    fig.update_xaxes(tickfont=dict(size=12), title=xaxis_title, showgrid=True, tickformat='%M:%S')
    fig.update_yaxes(tickfont=dict(size=12), title=yaxis_title, showgrid=True, type=y_scale)
    fig.update_layout(title=chart_title, title_font=dict(size=12))
    fig.update_traces(opacity=OPACITY)

    if meta is None:
        streamlit.plotly_chart(fig, use_container_width=True)
        return

    # plot metadata
    for i in range(0, len(meta) - 1, 2):
        x0, x1 = pandas.to_datetime(meta.loc[i:i+1, "rel"], unit="ms", origin="unix")
        name = meta.at[i, "event"]
        fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(255,255,0,0.1)", 
                      annotation_text=name, 
                      line_width=0, annotation_position="bottom right")

    streamlit.plotly_chart(fig, use_container_width=True)
    return



def __mean_variable_trend(media: pandas.DataFrame,
                          noise: pandas.DataFrame, x: str, y: str, 
                          xaxis_title: str,
                          yaxis_title: str,
                          chart_title: str, y_log=False):

    def add_trace(data: dict, color: str, dash=None, name_suffix=""):
        for i, (rate, frame) in enumerate(data.items()):
            # process and aggregate data
            data = (frame[frame[y] != 0]
                          .assign(**{x: frame[x] / 1000})
                          .groupby(x, as_index=False)[y].mean())
            data[x] = pandas.to_datetime(data[x], origin="unix", unit='s')

            mode = 'lines' if dash is not None else 'lines+markers'
            marker = dict(color=color[i], size=1  if dash is not None else 0.5)
            line   = dict(color=color[i], width=1 if dash is not None else 1, dash=dash)

            # add trace to the figure
            fig.add_trace(go.Scatter(
                x=data[x], 
                y=data[y], 
                mode=mode, marker=marker, line=line,
                name=f"{rate} kbits{name_suffix}" if rate != 'infi' else f"no-limits{name_suffix}"))

    # create figure
    fig = go.Figure()

    # plot media traces
    add_trace(media, TESTBED_RATES_COLORS)

    # plot noise traces if available
    if noise:
        add_trace(noise, TESTBED_RATES_COLORS, dash='dot', name_suffix=" (noise)")

    # configure axes and layout
    fig.update_xaxes(tickfont=dict(size=12), title=xaxis_title, showgrid=True, tickformat="%M:%S")
    fig.update_yaxes(tickfont=dict(size=12), title=yaxis_title, showgrid=True, type='log' if y_log else 'linear')
    fig.update_traces(opacity=OPACITY)
    fig.update_layout(title=chart_title, title_font=dict(size=12))

    # render plot in Streamlit
    streamlit.plotly_chart(fig, use_container_width=True)


def __timeline(data: pandas.DataFrame, 
               meta: pandas.DataFrame | None, 
               xs: str, 
               xe: str, y: str, 
               color: str,
               xaxis_title: str,
               yaxis_title: str,
               chart_title: str, info: str | None, legend=True, theme=None, y_log=None):
    
    # generate a timeline figure
    fig = px.timeline(data_frame=data, 
                      x_start=xs, 
                      x_end=xe, 
                      y=y, color=color, 
                      custom_data=[info] if info is not None else None, template=TEMPLATE)

    # add the description
    if info is not None:
        fig.update_traces(hovertemplate="%{customdata[0]}")

    # config x-axis
    if meta is not None:
        values, labels = timeline_axis(min_value=pandas.Timestamp('1970-01-01 00:00:00'),
                                       max_value=pandas.to_datetime(meta["rel"].max(), unit="ms", origin="unix"))
    else:
        values, labels = timeline_axis(min_value=data[xs].min(), max_value=data[xe].max())
        
    # determine the number of unique y-axis values
    num = len(data[y].unique())
    
    # adjust the height based on the number of y-axis values
    if num < 10:
        fig.update_layout(height=300)  # adjust height for fewer y-axis values
    else:
        fig.update_layout(height=500)  # adjust height for more y-axis values

    # set the x-axis
    fig.update_xaxes(tickvals=values, 
                     ticktext=labels, 
                     tickfont=dict(size=12), title=xaxis_title, showgrid=True)
    
    # set the y-axis
    fig.update_yaxes(tickfont=dict(size=12), title=yaxis_title, showgrid=True)

    # set the opacity
    fig.update_traces(opacity=OPACITY)
    # set the title
    fig.update_layout(title=chart_title, title_font=dict(size=12), showlegend=legend)

    if meta is None:
        # show the plot
        streamlit.plotly_chart(fig, theme=theme, use_container_width=True)

    # plot metadata
    for i in range(0, len(meta) - 1, 2):
        x0, x1 = pandas.to_datetime(meta.loc[i:i+1, "rel"], unit="ms", origin="unix")
        name = meta.at[i, "event"]
        fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(255,255,0,0.1)", 
                      annotation_text=name, 
                      line_width=0, annotation_position="bottom right")

    # show the plot
    streamlit.plotly_chart(fig, theme=theme, use_container_width=True)

def __cumulative_function(x: str,
                          xaxis_title: str, 
                          yaxis_title: str,
                          chart_title: str, data: dict, noise: dict | None):
    # init a new figure
    fig = go.Figure()

    # compute the cdf
    for i, (rate, frame) in enumerate(data.items()):
        values = numpy.sort(frame[x])
        cumuls = numpy.arange(1, len(values) + 1) / len(values)

        fig.add_trace(go.Scatter(
            x=values, 
            y=cumuls,
            mode='lines+markers',
            marker=dict(color=TESTBED_RATES_COLORS[i], size=0.8), 
            line=dict(color=TESTBED_RATES_COLORS[i], width=1),
            name=f"{rate} kbits" if rate != 'infi' else "no-limits"))
    
    if noise is not None:
        for i, (rate, frame) in enumerate(noise.items()):
            values = numpy.sort(frame[x])
            cumuls = numpy.arange(1, len(values) + 1) / len(values)

            fig.add_trace(go.Scatter(
                x=values, 
                y=cumuls,
                mode='lines',
                line=dict(color=TESTBED_RATES_COLORS[i], width=0.5, dash='dash'),
                name=f"{rate} kbits" if rate != 'infi' else "no-limits"))

    fig.update_xaxes(title=xaxis_title, showgrid=True, type='log')
    fig.update_yaxes(title=yaxis_title, showgrid=True)
    fig.update_layout(title=chart_title, title_font=dict(size=12), 
                      showlegend=True, legend_title="testbed bitrate traces")

    streamlit.plotly_chart(fig, use_container_width=True)
