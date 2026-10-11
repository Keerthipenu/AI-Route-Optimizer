from __future__ import annotations

from typing import Sequence

import pandas as pd
import plotly.graph_objects as go

from .integrations import RoadRoute
from .models import AlgorithmResult, Location

ACCENT = "#C7F464"
PANEL = "#171A17"
MUTED = "#90998B"


def route_figure(
    result: AlgorithmResult,
    locations: Sequence[Location],
    road_route: RoadRoute | None = None,
) -> go.Figure:
    route_locations = [locations[index] for index in result.route]
    figure = go.Figure()
    line_lons = (
        [longitude for latitude, longitude in road_route.coordinates]
        if road_route else [location.longitude for location in route_locations]
    )
    line_lats = (
        [latitude for latitude, longitude in road_route.coordinates]
        if road_route else [location.latitude for location in route_locations]
    )
    figure.add_trace(go.Scatter(
        x=line_lons,
        y=line_lats,
        mode="lines",
        line={"color": ACCENT, "width": 4},
        hovertemplate=("Road-network route" if road_route else "Great-circle route") + "<extra></extra>",
        name=result.algorithm,
    ))
    figure.add_trace(go.Scatter(
        x=[location.longitude for location in route_locations],
        y=[location.latitude for location in route_locations],
        mode="markers+text",
        marker={"size": 10, "color": PANEL, "line": {"color": ACCENT, "width": 2}},
        text=[str(i) for i in range(len(route_locations))], textposition="top center",
        customdata=[[location.name, location.location_id] for location in route_locations],
        hovertemplate="<b>%{customdata[0]}</b><br>ID %{customdata[1]}<br>%{y:.4f}, %{x:.4f}<extra></extra>",
        name="Stops",
    ))
    depot = route_locations[0]
    figure.add_trace(go.Scatter(
        x=[depot.longitude], y=[depot.latitude], mode="markers",
        marker={"size": 19, "color": ACCENT, "symbol": "square"}, name="Depot",
        hovertemplate=f"<b>{depot.name}</b><br>Depot<extra></extra>",
    ))
    figure.update_layout(
        height=520,
        margin={"l": 12, "r": 12, "t": 12, "b": 12},
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font={"color": "#E9ECE4"},
        xaxis={"title": "Longitude", "gridcolor": "#30352E", "zeroline": False},
        yaxis={"title": "Latitude", "gridcolor": "#30352E", "zeroline": False, "scaleanchor": "x", "scaleratio": 1},
        legend={"orientation": "h", "x": 0.01, "y": 0.99, "bgcolor": "rgba(0,0,0,0)"},
    )
    return figure


def comparison_figure(table: pd.DataFrame) -> go.Figure:
    figure = go.Figure(go.Bar(
        x=table["Distance (km)"], y=table["Algorithm"], orientation="h",
        marker_color=[ACCENT if name != "Nearest Neighbor" else "#6E766A" for name in table["Algorithm"]],
        text=table["Distance (km)"].map(lambda value: f"{value:.2f} km"), textposition="outside",
    ))
    figure.update_layout(
        height=300, margin={"l": 10, "r": 60, "t": 10, "b": 35},
        paper_bgcolor=PANEL, plot_bgcolor=PANEL, font={"color": "#E9ECE4"},
        xaxis={"title": "Route distance (km)", "gridcolor": "#30352E"},
        yaxis={"autorange": "reversed"}, showlegend=False,
    )
    return figure


def annealing_history_figure(result: AlgorithmResult) -> go.Figure:
    history = pd.DataFrame(result.history)
    figure = go.Figure()
    if not history.empty:
        figure.add_trace(go.Scatter(x=history["iteration"], y=history["best_distance"], name="Best distance", line={"color": ACCENT, "width": 3}))
        figure.add_trace(go.Scatter(x=history["iteration"], y=history["temperature"], name="Temperature", yaxis="y2", line={"color": "#F39A55", "width": 2}))
    figure.update_layout(
        height=340, margin={"l": 10, "r": 10, "t": 20, "b": 35},
        paper_bgcolor=PANEL, plot_bgcolor=PANEL, font={"color": "#E9ECE4"},
        xaxis={"title": "Iteration", "gridcolor": "#30352E"},
        yaxis={"title": "Best distance (km)", "gridcolor": "#30352E"},
        yaxis2={"title": "Temperature", "overlaying": "y", "side": "right", "showgrid": False},
        legend={"orientation": "h", "y": 1.08},
    )
    return figure
