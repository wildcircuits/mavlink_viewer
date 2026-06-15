#!/usr/bin/env python3
"""Real-time WaterDist heatmap dashboard using Dash + Plotly.

Usage:
    source .venv/bin/activate && python3 visualize.py

Then open http://127.0.0.1:8050 in your browser.

The dashboard auto-refreshes every 3 seconds as new CSV data arrives.
"""

import csv
import os
import glob
import time
from datetime import datetime, timezone

import dash
from dash import html, dcc, Input, Output, callback_context
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Find the latest CSV file
def get_latest_csv():
    """Find the most recent waterdist_capture_*.csv file."""
    files = glob.glob("waterdist_capture_*.csv")
    if not files:
        return None
    return sorted(files)[-1]


def read_csv(filepath, min_dist):
    """Read CSV and return list of dicts with numeric lat/lon."""
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = float(row["gps_lat"]) if row["gps_lat"] else None
            lon = float(row["gps_lon"]) if row["gps_lon"] else None
            try:
                wd = float(row["WaterDist"])
            except (ValueError, KeyError):
                wd = None
            if lat is not None and lon is not None and wd is not None and wd > min_dist:
                rows.append({
                    "lat": lat,
                    "lon": lon,
                    "WaterDist": wd,
                    "timestamp": row["timestamp"],
                })
    print(f'read CSV and found {len(rows)} number of point above min distance level of {min_dist}')
    return rows


def make_fig(rows):
    """Create a scatter plot colored by WaterDist value."""
    if not rows:
        fig = go.Figure()
        fig.add_annotation(text="No data yet. Waiting for GPS lock + WaterDist...",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=16))
        fig.update_layout(xaxis_title="Longitude", yaxis_title="Latitude",
                          height=600)
        return fig

    df = rows[-2000:]  # limit to last 1000 points for performance

    fig = px.scatter(df, x="lon", y="lat", color="WaterDist",
                     color_continuous_scale="Viridis",
                     labels={"WaterDist": "WaterDist"},
                     title=f"WaterDist Heatmap ({len(df)} points)",
                     hover_data={"timestamp": True},
                     opacity=0.8)

    fig.update_layout(
        height=600,
        coloraxis_colorbar_title="WaterDist",
        coloraxis_colorbar_tickformat=".1f",
        xaxis_title="Longitude",
        yaxis_title="Latitude",
    )
    return fig


def make_summary_fig(rows):
    """Create a histogram of WaterDist values."""
    if not rows:
        fig = go.Figure()
        fig.add_annotation(text="No data yet.", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    wd_values = [r["WaterDist"] for r in rows]
    fig = go.Figure(data=go.Histogram(x=wd_values, nbinsx=100,
                                       marker_color="steelblue"))
    fig.update_layout(
        title="WaterDist Distribution",
        xaxis_title="WaterDist",
        yaxis_title="Count",
        height=300,
    )
    return fig


# Initialize Dash app
app = dash.Dash(__name__, title="WaterDist Heatmap")

# Build layout
app.layout = html.Div([
    html.H1("WaterDist Heatmap Dashboard",
            style={"textAlign": "center", "marginBottom": 10}),

    html.Div([
        html.Span("CSV: ", style={"fontWeight": "bold"}),
        html.Span(id="csv-status", children="No CSV file found",
                  style={"fontWeight": "normal"}),
        html.Span("  |  Refresh: ", style={"fontWeight": "bold"}),
        html.Span(id="last-refresh", children="",
                  style={"fontWeight": "normal"}),
    ], style={"textAlign": "center", "marginBottom": 10}),

    dcc.Interval(
        id="interval",
        interval=3 * 1000,  # 3 seconds
        n_intervals=0,
    ),

    html.Div([
        dcc.Graph(id="scatter-plot", config={"displayModeBar": False}),
    ], style={"marginBottom": 10}),

    html.Div([
        dcc.Graph(id="histogram-plot", config={"displayModeBar": False}),
    ]),
])


@app.callback(
    [Output("scatter-plot", "figure"),
     Output("histogram-plot", "figure"),
     Output("csv-status", "children"),
     Output("last-refresh", "children")],
    Input("interval", "n_intervals"),
)
def update(n):
    csv_file = get_latest_csv()
    if csv_file is None:
        return (
            make_fig([]),
            make_summary_fig([]),
            "No CSV file found",
            "",
        )

    rows = read_csv(csv_file, min_dist=100)
    now = datetime.now().strftime("%H:%M:%S")

    fig_scatter = make_fig(rows)
    fig_hist = make_summary_fig(rows)

    return (
        fig_scatter,
        fig_hist,
        f"{csv_file} ({len(rows)} points)",
        f"Updated: {now}",
    )


if __name__ == "__main__":
    print("Starting dashboard on http://127.0.0.1:8050 ...")
    app.run(host="127.0.0.1", port=8050, debug=False)
