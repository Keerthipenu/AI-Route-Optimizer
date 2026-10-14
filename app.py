from __future__ import annotations

from hashlib import sha256
import os

import streamlit as st

from src.data_loader import load_csv
from src.distance import build_distance_matrix
from src.integrations import DEFAULT_OSRM_URL, ProviderError, fetch_osrm_matrix
from src.models import RouteConstraints
from src.objectives import RouteObjective
from src.ui.components import brand
from src.ui.pages import algorithm_lab_page, delivery_data_page, plan_page, tracking_page
from src.ui.theme import inject_theme
from src.validation import DataValidationError, frame_to_locations, validate_delivery_frame

st.set_page_config(page_title="ROUTEFORGE", page_icon="R", layout="wide", initial_sidebar_state="expanded")
inject_theme(st)

with st.sidebar:
    brand(st)
    page = st.radio("WORKSPACE", ["Plan a Route", "Algorithm Lab", "Live Tracking", "Delivery Data"], label_visibility="collapsed")
    st.divider()
    upload = st.file_uploader("Upload delivery dataset", type=["csv"])
    st.download_button(
        "DOWNLOAD CSV TEMPLATE",
        "location_id,name,latitude,longitude,priority,service_duration\n",
        "routeforge-template.csv",
        "text/csv",
        width="stretch",
    )
    st.caption("Upload a CSV to validate its schema and configure a route. No delivery locations are preloaded.")

if upload is None:
    st.info("Upload a delivery CSV from the sidebar to begin. The application validates the dataset before enabling route planning.")
    st.stop()

with st.sidebar:
    upload_bytes = upload.getvalue()
    source_key = f"upload:{upload.name}:{sha256(upload_bytes).hexdigest()}"
    if st.session_state.get("source_key") != source_key:
        try:
            st.session_state.delivery_frame = load_csv(upload_bytes)
            st.session_state.source_key = source_key
            st.session_state.pop("report", None)
        except DataValidationError as exc:
            st.error(str(exc))
            st.session_state.pop("delivery_frame", None)
            st.stop()
    frame = st.session_state.delivery_frame
    st.caption(f"{len(frame)} locations · edits are local to this session")

try:
    if page == "Delivery Data":
        frame = delivery_data_page(frame)
        st.session_state.delivery_frame = frame
    clean_frame = validate_delivery_frame(frame)
    locations = frame_to_locations(clean_frame)
except DataValidationError as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    labels = [f"{location.location_id} · {location.name}" for location in locations]
    depot_label = st.selectbox("Depot", labels, index=0)
    depot_index = labels.index(depot_label)
    route_mode = st.radio("Route mode", ["Round trip", "One way"], horizontal=True)
    end_index = None
    if route_mode == "One way" and len(locations) > 1:
        endpoint_labels = [label for index, label in enumerate(labels) if index != depot_index]
        fixed = st.checkbox("Fix final destination", value=False)
        if fixed:
            endpoint_label = st.selectbox("Final destination", endpoint_labels)
            end_index = labels.index(endpoint_label)
    with st.expander("Optimization settings"):
        seed = st.number_input("Random seed", min_value=0, max_value=1_000_000, value=42, step=1)
        iterations = st.slider("Annealing iterations", 500, 20_000, 5_000, 500)
        brute_force_limit = st.slider("Brute Force safety limit", 3, 10, 8)
        objective_label = st.selectbox(
            "Optimization objective",
            ["Shortest distance", "Fastest route", "Priority-weighted arrival"],
        )
        assumed_speed_kph = st.number_input(
            "Offline speed assumption (km/h)", min_value=5.0, max_value=130.0, value=35.0, step=5.0,
            help="Used only for offline ETA and time-based objectives.",
        )
    st.markdown("<div class='rf-section'>Distance model</div>", unsafe_allow_html=True)
    distance_choice = st.radio(
        "Distance model", ["Geographic · offline", "Road network · OSRM"],
        label_visibility="collapsed",
    )
    osrm_url = DEFAULT_OSRM_URL
    road_signature = clean_frame.to_csv(index=False)
    if distance_choice == "Road network · OSRM":
        osrm_url = st.text_input("OSRM server", value=DEFAULT_OSRM_URL)
        if st.button("LOAD / REFRESH ROAD MATRIX", width="stretch"):
            try:
                with st.spinner("Requesting road distances and travel times…"):
                    st.session_state.road_matrices = fetch_osrm_matrix(locations, osrm_url)
                    st.session_state.road_matrix_signature = (road_signature, osrm_url)
            except ProviderError as exc:
                st.error(str(exc))
        if st.session_state.get("road_matrix_signature") != (road_signature, osrm_url):
            st.caption("Load the matrix to switch from geographic to road-network optimization.")
    st.markdown("<div class='rf-section'>Map display</div>", unsafe_allow_html=True)
    map_provider = st.radio(
        "Map display", ["Google Maps", "Offline coordinate plot"],
        label_visibility="collapsed",
    )
    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    try:
        google_maps_key = google_maps_key or str(st.secrets.get("GOOGLE_MAPS_API_KEY", "")).strip()
    except (FileNotFoundError, KeyError):
        pass
    if map_provider == "Google Maps" and not google_maps_key:
        google_maps_key = st.text_input(
            "Google Maps API key",
            type="password",
            key="google_maps_key",
            help="Used in this browser session only. Restrict the key to Maps JavaScript API and your website referrers.",
        ).strip()
        if not google_maps_key:
            st.caption("Add a key to activate Google Maps; the offline map remains available.")

objective_mode = {
    "Shortest distance": "distance",
    "Fastest route": "fastest",
    "Priority-weighted arrival": "priority_weighted_eta",
}[objective_label]

constraints = RouteConstraints(depot_index=depot_index, round_trip=route_mode == "Round trip", end_index=end_index)
geographic_matrix = build_distance_matrix(locations)
road_mode = (
    distance_choice == "Road network · OSRM"
    and st.session_state.get("road_matrix_signature") == (road_signature, osrm_url)
)
road_matrices = st.session_state.get("road_matrices") if road_mode else None
matrix = road_matrices.distance_km if road_matrices is not None else geographic_matrix
duration_matrix = road_matrices.duration_seconds if road_matrices is not None else None
objective = RouteObjective(
    mode=objective_mode,
    duration_matrix=duration_matrix,
    locations=locations,
    assumed_speed_kph=float(assumed_speed_kph),
)
settings = {
    "seed": int(seed), "iterations": iterations, "brute_force_limit": brute_force_limit,
    "assumed_speed_kph": float(assumed_speed_kph), "duration_matrix": duration_matrix,
    "road_mode": road_mode, "osrm_url": osrm_url,
    "distance_source": road_matrices.provider if road_matrices is not None else "Haversine",
    "map_provider": map_provider, "google_maps_key": google_maps_key,
}
configuration_key = (
    clean_frame.to_csv(index=False), depot_index, route_mode, end_index,
    settings["seed"], settings["iterations"], settings["brute_force_limit"],
    objective_mode, settings["assumed_speed_kph"], settings["distance_source"],
)
if st.session_state.get("configuration_key") != configuration_key:
    st.session_state.configuration_key = configuration_key
    st.session_state.pop("report", None)

if page == "Plan a Route":
    plan_page(locations, matrix, constraints, settings, upload.name, objective)
elif page == "Algorithm Lab":
    algorithm_lab_page(locations, matrix, constraints, settings, objective)
elif page == "Live Tracking":
    tracking_page(locations, matrix, constraints, settings)
