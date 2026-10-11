from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..algorithms import brute_force, nearest_neighbor, simulated_annealing, two_opt
from ..evaluation import evaluate_algorithms, repeated_annealing
from ..export_utils import result_to_json, route_to_csv
from ..integrations import (
    ProviderError, fetch_osrm_route, fetch_tomtom_traffic_summary, geocode_address,
)
from ..models import RouteConstraints
from ..objectives import RouteObjective, total_route_minutes
from ..tracking import fetch_telemetry_feed, load_telemetry_csv, tracking_snapshot
from ..visualization import annealing_history_figure, comparison_figure, route_figure
from .components import explanation, hero, route_timeline


def overview_page(locations) -> None:
    hero(st, "OPERATIONS / OVERVIEW", "Route intelligence, without the black box", "A local, reproducible workspace for comparing exact and heuristic TSP solvers.")
    columns = st.columns(4)
    columns[0].metric("Active locations", len(locations))
    columns[1].metric("Optimization methods", "4")
    columns[2].metric("Distance model", "Haversine")
    columns[3].metric("External APIs", "None")
    st.markdown("### The workflow")
    steps = st.columns(4)
    for column, number, title, copy in zip(steps, ["01", "02", "03", "04"], ["Validate", "Measure", "Optimize", "Explain"], ["Check schema, IDs and coordinates.", "Build one shared distance matrix.", "Run consistent route constraints.", "Inspect route, evidence and gaps."]):
        column.markdown(f'<div class="rf-panel"><div class="rf-kicker">{number}</div><h3>{title}</h3><p class="rf-note">{copy}</p></div>', unsafe_allow_html=True)
    st.info("Distances are great-circle estimates between coordinates—not road-driving distances, traffic estimates, or live navigation data.")


def plan_page(locations, matrix, constraints, settings, dataset_name: str, objective: RouteObjective) -> None:
    model_label = "road-network distance" if settings["road_mode"] else "offline geographic distance"
    hero(st, "PLAN / ACTIVE ROUTE", f"{dataset_name.split('·')[0].strip()} delivery circuit", f"{len(locations)-1} destinations · depot fixed · {model_label} · {objective.label.replace('_', ' ')}")
    left, right = st.columns([1.3, 1])
    with left:
        mode = st.segmented_control("Optimization mode", ["Compare all", "Nearest Neighbor", "2-opt", "Simulated Annealing", "Brute Force"], default="Compare all")
    with right:
        optimize = st.button("OPTIMIZE ROUTE", type="primary", use_container_width=True)
    if optimize:
        requested = ["Nearest Neighbor", "2-opt", "Simulated Annealing", "Brute Force"] if mode == "Compare all" else [mode]
        try:
            st.session_state.report = evaluate_algorithms(
                matrix, constraints, requested, seed=settings["seed"],
                sa_iterations=settings["iterations"], brute_force_limit=settings["brute_force_limit"],
                objective=objective,
            )
        except ValueError as exc:
            st.error(str(exc))
            return
    report = st.session_state.get("report")
    if report is None:
        st.markdown('<div class="rf-callout"><b>Ready to optimize.</b><br>Select a method and run the route. Results are calculated locally from the current data.</div>', unsafe_allow_html=True)
        return
    names = [result.algorithm for result in report.results]
    selected_name = st.selectbox("Inspect solution", names, index=min(1, len(names)-1))
    result = next(item for item in report.results if item.algorithm == selected_name)
    baseline = next((item for item in report.results if item.algorithm == "Nearest Neighbor"), result)
    exact_row = report.table.loc[report.table["Algorithm"] == "Brute Force"]
    selected_row = report.table.loc[report.table["Algorithm"] == result.algorithm]
    objective_gap = None if exact_row.empty else float(selected_row.iloc[0]["Optimality gap (%)"])
    eta_minutes = total_route_minutes(
        result.route, matrix, locations, settings.get("duration_matrix"), settings["assumed_speed_kph"]
    )
    service_minutes = sum(location.service_duration or 0 for location in locations if location != locations[constraints.depot_index])
    metric_row_one = st.columns(3)
    metric_row_one[0].metric("Route distance", f"{result.total_distance:.2f} km")
    metric_row_one[1].metric("Delivery stops", len(locations) - 1)
    metric_row_one[2].metric("Saved vs baseline", f"{max(0.0, baseline.total_distance-result.total_distance):.2f} km")
    metric_row_two = st.columns(3)
    metric_row_two[0].metric("Execution time", f"{result.runtime_seconds*1000:.2f} ms")
    metric_row_two[1].metric("Exact gap", "—" if objective_gap is None else f"{objective_gap:.2f}%")
    metric_row_two[2].metric("Estimated route time", f"{eta_minutes:.0f} min")
    metric_row_three = st.columns(2)
    metric_row_three[0].metric("Included service time", f"{service_minutes:.0f} min")
    metric_row_three[1].metric("Distance source", settings["distance_source"])
    road_route = None
    if settings["road_mode"]:
        road_key = (tuple(result.route), settings["osrm_url"])
        if st.session_state.get("road_route_key") != road_key:
            try:
                with st.spinner("Fetching road geometry…"):
                    st.session_state.road_route = fetch_osrm_route(
                        result.route, locations, settings["osrm_url"]
                    )
                    st.session_state.road_route_key = road_key
            except ProviderError as exc:
                st.warning(str(exc))
                st.session_state.road_route = None
        road_route = st.session_state.get("road_route")
    map_col, timeline_col = st.columns([1.7, 1])
    with map_col:
        st.plotly_chart(route_figure(result, locations, road_route), use_container_width=True, config={"displayModeBar": False})
        if road_route:
            st.caption(f"Road geometry from {road_route.provider}; {road_route.distance_km:.2f} km and {road_route.duration_minutes:.0f} minutes without a live-traffic guarantee.")
        else:
            st.caption("Offline coordinate plot. Route segments show great-circle estimates, not roads.")
    with timeline_col:
        route_timeline(st, result, locations, matrix)
    st.markdown(f'<div class="rf-callout"><div class="rf-kicker">WHY THIS ROUTE?</div><br>{explanation(result)}</div>', unsafe_allow_html=True)
    with st.expander("Live traffic · optional TomTom connection"):
        st.caption("Traffic values are requested from TomTom only when you provide your own key and press refresh. The key stays in this Streamlit session and is not written to disk.")
        traffic_key = st.text_input("TomTom API key", type="password", key="tomtom_key")
        if st.button("REFRESH LIVE TRAFFIC", disabled=not bool(traffic_key)):
            try:
                with st.spinner("Requesting current traffic…"):
                    st.session_state.traffic_summary = fetch_tomtom_traffic_summary(
                        result.route, locations, traffic_key
                    )
                    st.session_state.traffic_summary_key = tuple(result.route)
            except ProviderError as exc:
                st.error(str(exc))
        traffic = (
            st.session_state.get("traffic_summary")
            if st.session_state.get("traffic_summary_key") == tuple(result.route)
            else None
        )
        if traffic:
            traffic_cols = st.columns(4)
            traffic_cols[0].metric("Traffic travel time", f"{traffic.travel_time_minutes:.0f} min")
            traffic_cols[1].metric("Traffic delay", "—" if traffic.traffic_delay_minutes is None else f"{traffic.traffic_delay_minutes:.0f} min")
            traffic_cols[2].metric("No-traffic time", "—" if traffic.no_traffic_minutes is None else f"{traffic.no_traffic_minutes:.0f} min")
            traffic_cols[3].metric("Traffic route", f"{traffic.distance_km:.1f} km")
            st.caption(f"Provider: {traffic.provider}. Departure {traffic.departure_time or 'not returned'}; arrival {traffic.arrival_time or 'not returned'}.")
    if len(report.results) > 1:
        st.markdown("### Algorithm comparison")
        chart_col, table_col = st.columns([1, 1.2])
        with chart_col:
            st.plotly_chart(comparison_figure(report.table), use_container_width=True, config={"displayModeBar": False})
        with table_col:
            st.dataframe(report.table.style.format({"Distance (km)":"{:.3f}", "Runtime (ms)":"{:.3f}", "Improvement vs NN (%)":"{:.2f}", "Optimality gap (%)":"{:.2f}"}, na_rep="—"), use_container_width=True, hide_index=True)
        st.caption("Work counts have algorithm-specific meanings and should not be compared as equivalent units of computational cost.")
    csv_col, json_col, _ = st.columns([1, 1, 2])
    csv_col.download_button("Export route CSV", route_to_csv(result, locations, matrix), "routeforge-route.csv", "text/csv", use_container_width=True)
    json_col.download_button("Export result JSON", result_to_json(result, locations, matrix), "routeforge-result.json", "application/json", use_container_width=True)


def algorithm_lab_page(locations, matrix, constraints, settings, objective: RouteObjective) -> None:
    hero(st, "ALGORITHM / LAB", "Watch the search change the route", "Inspect recorded decisions and convergence without blocking animations.")
    tabs = st.tabs(["Nearest Neighbor", "2-opt", "Simulated Annealing", "Brute Force"])
    nn = nearest_neighbor(matrix, constraints, objective)
    with tabs[0]:
        st.markdown("#### Greedy construction history")
        history = pd.DataFrame(nn.history)
        if not history.empty:
            history["current"] = history["current"].map(lambda index: locations[index].name)
            history["selected"] = history["selected"].map(lambda index: locations[index].name)
        st.dataframe(history, use_container_width=True, hide_index=True)
        st.info("Complexity: O(n²). Fast and deterministic; no optimality guarantee.")
    with tabs[1]:
        result = two_opt(matrix, constraints, initial_route=nn.route, objective=objective)
        st.metric("Improvement over initial route", f"{result.metadata['improvement_km']:.3f} km")
        st.dataframe(pd.DataFrame(result.history), use_container_width=True, hide_index=True)
        st.info("Typical implementation cost: O(k·n²) candidate checks for k passes. Returns a local optimum.")
    with tabs[2]:
        result = simulated_annealing(matrix, constraints, initial_route=nn.route, seed=settings["seed"], iterations=settings["iterations"], objective=objective)
        st.plotly_chart(annealing_history_figure(result), use_container_width=True, config={"displayModeBar": False})
        st.caption("Distance and temperature are different units and use separate axes. The seed makes this run reproducible.")
    with tabs[3]:
        if len(locations) - 1 <= settings["brute_force_limit"]:
            result = brute_force(matrix, constraints, settings["brute_force_limit"], objective)
            st.metric("Exact optimum", f"{result.total_distance:.3f} km")
            st.write(f"Evaluated {result.work_count:,} permitted permutations; {result.metadata['optimal_tie_count']} route(s) tied at the optimum.")
        else:
            st.warning(f"Disabled: {len(locations)-1} destinations exceeds the safety limit of {settings['brute_force_limit']}.")


def benchmarks_page(locations, matrix, constraints, settings, objective: RouteObjective) -> None:
    hero(st, "RESEARCH / BENCHMARKS", "Reproducible experiment bench", "Compare route quality and measure annealing variability with documented seeds.")
    seeds_text = st.text_input("Simulated Annealing seeds", "11, 22, 33, 44, 55")
    if st.button("RUN BENCHMARK", type="primary"):
        try:
            seeds = [int(item.strip()) for item in seeds_text.split(",") if item.strip()]
            if not seeds:
                raise ValueError("Provide at least one integer seed.")
            report = evaluate_algorithms(matrix, constraints, seed=settings["seed"], sa_iterations=settings["iterations"], brute_force_limit=settings["brute_force_limit"], objective=objective)
            repeats = repeated_annealing(matrix, constraints, seeds, settings["iterations"], objective)
            st.session_state.benchmark = (report, repeats)
        except ValueError as exc:
            st.error(str(exc))
    if "benchmark" in st.session_state:
        report, repeats = st.session_state.benchmark
        st.dataframe(report.table, use_container_width=True, hide_index=True)
        st.markdown("#### Simulated Annealing variability")
        st.dataframe(repeats, use_container_width=True, hide_index=True)
        stats = repeats["distance_km"].agg(["mean", "min", "max", "std"])
        columns = st.columns(4)
        for column, label in zip(columns, ["mean", "min", "max", "std"]):
            value = stats[label]
            column.metric(label.upper(), "—" if pd.isna(value) else f"{value:.3f} km")
        payload = {"environment": report.metadata, "comparison": report.table.to_dict(orient="records"), "annealing_runs": repeats.to_dict(orient="records")}
        st.download_button("Export benchmark JSON", json.dumps(payload, indent=2).encode(), "routeforge-benchmark.json", "application/json")
        st.caption("Runtime is machine- and implementation-dependent. Only measured values from this execution are shown.")


def delivery_data_page(frame: pd.DataFrame) -> pd.DataFrame:
    hero(st, "DATA / LOCATIONS", "Delivery dataset", "Edit destinations directly. Duplicate coordinates are valid; duplicate IDs are not.")
    with st.expander("Add a destination from an address"):
        st.caption("Explicit searches use OpenStreetMap Nominatim with caching and a one-request-per-second guard. Do not submit personal or confidential addresses.")
        query = st.text_input("Address or place", placeholder="Example: Vidhana Soudha, Bengaluru")
        if st.button("SEARCH ADDRESS", disabled=len(query.strip()) < 3):
            try:
                st.session_state.geocode_results = geocode_address(query)
            except ProviderError as exc:
                st.error(str(exc))
        results = st.session_state.get("geocode_results", [])
        if results:
            selected_label = st.selectbox("Match", [item["display_name"] for item in results])
            match = next(item for item in results if item["display_name"] == selected_label)
            new_id = st.text_input("New location ID", value=f"GEO-{len(frame):03d}")
            new_name = st.text_input("Display name", value=str(selected_label).split(",")[0])
            if st.button("ADD GEOCODED LOCATION"):
                row = {
                    "location_id": new_id, "name": new_name,
                    "latitude": match["latitude"], "longitude": match["longitude"],
                    "priority": 2, "service_duration": 10,
                }
                st.session_state.delivery_frame = pd.concat([frame, pd.DataFrame([row])], ignore_index=True)
                st.session_state.pop("geocode_results", None)
                st.rerun()
        st.markdown("[Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) · © OpenStreetMap contributors")
    edited = st.data_editor(frame, num_rows="dynamic", use_container_width=True, hide_index=True, key="delivery_editor")
    st.markdown("#### CSV schema")
    st.code("location_id,name,latitude,longitude,priority,service_duration", language="text")
    st.caption("Required: location_id, name, latitude, longitude. Priority and service_duration are optional non-negative values.")
    return edited


def tracking_page(locations, matrix, constraints) -> None:
    hero(st, "OPERATIONS / TRACKING", "Delivery telemetry", "Monitor the latest positions actually received from a CSV or HTTP JSON/CSV GPS feed.")
    st.warning("ROUTEFORGE does not invent vehicle movement. The included telemetry is clearly marked sample data; live mode requires a real device or fleet endpoint.")
    source = st.radio("Telemetry source", ["Sample telemetry", "Upload CSV", "HTTP feed"], horizontal=True)
    telemetry = None
    try:
        if source == "Sample telemetry":
            telemetry = pd.read_csv("data/sample_telemetry.csv")
        elif source == "Upload CSV":
            upload = st.file_uploader("GPS telemetry CSV", type=["csv"], key="telemetry_upload")
            if upload:
                telemetry = load_telemetry_csv(upload.getvalue())
        else:
            feed_url = st.text_input("Telemetry endpoint URL", placeholder="https://fleet.example.com/positions.json")
            if st.button("FETCH LATEST GPS", disabled=not feed_url):
                st.session_state.telemetry = fetch_telemetry_feed(feed_url)
            telemetry = st.session_state.get("telemetry")
    except (ValueError, ProviderError) as exc:
        st.error(str(exc))
    if telemetry is None:
        st.info("Connect or upload a feed to display vehicle positions.")
        return
    route = nearest_neighbor(matrix, constraints).route
    try:
        snapshot = tracking_snapshot(telemetry, route, locations)
    except ValueError as exc:
        st.error(str(exc))
        return
    cols = st.columns(3)
    cols[0].metric("Vehicles reporting", len(snapshot))
    cols[1].metric("At a planned stop", int(snapshot["at_stop"].sum()))
    last_update = snapshot["last_update"].max()
    cols[2].metric("Latest update", last_update.strftime("%H:%M:%S UTC"))
    figure = route_figure(nearest_neighbor(matrix, constraints), locations)
    figure.add_trace(go.Scatter(
        x=snapshot["longitude"], y=snapshot["latitude"], mode="markers+text",
        marker={"size": 16, "color": "#F39A55", "symbol": "diamond"},
        text=snapshot["vehicle_id"], textposition="bottom center", name="Vehicles",
        customdata=snapshot[["reported_status", "last_update"]].astype(str).values,
        hovertemplate="<b>%{text}</b><br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
    ))
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
    st.dataframe(snapshot, use_container_width=True, hide_index=True)
    st.caption("A vehicle is marked at a stop when its latest coordinate is within 250 metres. This is proximity evidence, not proof of delivery completion.")


def about_page() -> None:
    hero(st, "GUIDE / METHODS", "The algorithms behind ROUTEFORGE", "Viva-ready explanations of what each method does—and what it cannot promise.")
    content = {
        "Nearest Neighbor": ("Repeatedly visits the closest unvisited stop.", "O(n²)", "No", "Fast baseline and live demos."),
        "Brute Force": ("Enumerates every permitted destination order.", "O(n! · n)", "Yes, within the fully evaluated constrained space", "Small exact benchmarks."),
        "2-opt": ("Reverses route segments whenever doing so shortens the route.", "O(k · n²)", "No", "Strong, explainable local improvement."),
        "Simulated Annealing": ("Samples neighbors and sometimes accepts worse moves according to temperature.", "O(iterations · n)", "No", "Escaping local optima and studying stochastic search."),
    }
    for name, (idea, complexity, guarantee, use) in content.items():
        with st.expander(name, expanded=name == "Nearest Neighbor"):
            st.write(idea)
            st.markdown(f"**Complexity:** `{complexity}`  \n**Global optimum guaranteed:** {guarantee}  \n**Useful for:** {use}")
    st.warning("ROUTEFORGE solves multi-stop tour ordering. That is different from A* or Greedy Best-First Search, which solve shortest paths through a graph between nodes.")
