from __future__ import annotations

from io import BytesIO
from typing import Sequence

import pandas as pd
import requests

from .distance import haversine_km
from .integrations import ProviderError, USER_AGENT
from .models import Location

TRACKING_COLUMNS = ("timestamp", "vehicle_id", "latitude", "longitude")


def validate_telemetry(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        raise ValueError("The telemetry feed is empty.")
    clean = frame.copy()
    clean.columns = [str(column).strip().lower() for column in clean.columns]
    missing = [column for column in TRACKING_COLUMNS if column not in clean.columns]
    if missing:
        raise ValueError(f"Missing telemetry columns: {', '.join(missing)}.")
    clean["timestamp"] = pd.to_datetime(clean["timestamp"], errors="coerce", utc=True)
    clean["latitude"] = pd.to_numeric(clean["latitude"], errors="coerce")
    clean["longitude"] = pd.to_numeric(clean["longitude"], errors="coerce")
    if clean[list(TRACKING_COLUMNS)].isnull().any().any():
        raise ValueError("Telemetry contains blank, malformed, or invalid timestamp/coordinate values.")
    for row in clean.itertuples(index=False):
        haversine_km(row.latitude, row.longitude, row.latitude, row.longitude)
    if "status" not in clean:
        clean["status"] = "in_transit"
    return clean.sort_values("timestamp").reset_index(drop=True)


def load_telemetry_csv(data: bytes) -> pd.DataFrame:
    try:
        return validate_telemetry(pd.read_csv(BytesIO(data)))
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Telemetry CSV could not be read: {exc}") from exc


def fetch_telemetry_feed(url: str, timeout: float = 10.0, session=requests) -> pd.DataFrame:
    if not url.lower().startswith(("http://", "https://")):
        raise ProviderError("Telemetry feed URL must use HTTP or HTTPS.")
    try:
        response = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            payload = response.json()
            rows = payload.get("positions", payload) if isinstance(payload, dict) else payload
            return validate_telemetry(pd.DataFrame(rows))
        return validate_telemetry(pd.read_csv(BytesIO(response.content)))
    except (requests.RequestException, ValueError, TypeError) as exc:
        raise ProviderError(f"Telemetry feed request failed: {exc}") from exc


def tracking_snapshot(
    telemetry: pd.DataFrame,
    route: Sequence[int],
    locations: Sequence[Location],
    arrival_radius_km: float = 0.25,
) -> pd.DataFrame:
    clean = validate_telemetry(telemetry)
    rows = []
    for vehicle_id, group in clean.groupby("vehicle_id", sort=True):
        latest = group.iloc[-1]
        candidates = []
        for sequence, index in enumerate(route):
            location = locations[index]
            distance = haversine_km(
                float(latest.latitude), float(latest.longitude), location.latitude, location.longitude
            )
            candidates.append((distance, sequence, location))
        nearest_distance, nearest_sequence, nearest = min(candidates, key=lambda item: item[0])
        rows.append({
            "vehicle_id": vehicle_id,
            "last_update": latest.timestamp,
            "latitude": float(latest.latitude),
            "longitude": float(latest.longitude),
            "nearest_route_stop": nearest.name,
            "route_sequence": nearest_sequence,
            "distance_to_stop_km": nearest_distance,
            "at_stop": nearest_distance <= arrival_radius_km,
            "reported_status": latest.status,
        })
    return pd.DataFrame(rows)
