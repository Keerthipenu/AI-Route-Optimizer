from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from threading import Lock
from time import monotonic, sleep
from typing import Sequence

import numpy as np
import requests

from .models import Location

DEFAULT_OSRM_URL = "https://router.project-osrm.org"
DEFAULT_NOMINATIM_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "ROUTEFORGE/1.1 educational-route-optimizer"


class ProviderError(RuntimeError):
    """A user-facing external provider failure."""


@dataclass(slots=True)
class RoadMatrices:
    distance_km: np.ndarray
    duration_seconds: np.ndarray
    provider: str
    snapped_names: list[str]


@dataclass(slots=True)
class TrafficSummary:
    distance_km: float
    travel_time_minutes: float
    traffic_delay_minutes: float | None
    no_traffic_minutes: float | None
    departure_time: str | None
    arrival_time: str | None
    provider: str = "TomTom Traffic"


@dataclass(slots=True)
class RoadRoute:
    coordinates: list[tuple[float, float]]
    distance_km: float
    duration_minutes: float
    provider: str = "OSRM driving profile"


def _coordinates(locations: Sequence[Location]) -> str:
    return ";".join(f"{item.longitude:.7f},{item.latitude:.7f}" for item in locations)


def fetch_osrm_matrix(
    locations: Sequence[Location],
    base_url: str = DEFAULT_OSRM_URL,
    timeout: float = 25.0,
    session=requests,
) -> RoadMatrices:
    if not 1 <= len(locations) <= 50:
        raise ProviderError("OSRM road matrices support 1–50 locations per request in ROUTEFORGE.")
    url = f"{base_url.rstrip('/')}/table/v1/driving/{_coordinates(locations)}"
    try:
        response = session.get(
            url,
            params={"annotations": "distance,duration", "fallback_speed": 13.9},
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ProviderError(f"OSRM request failed: {exc}") from exc
    if payload.get("code") != "Ok":
        raise ProviderError(f"OSRM could not build a route matrix: {payload.get('message', payload.get('code'))}")
    distances = payload.get("distances")
    durations = payload.get("durations")
    if not distances or not durations or any(value is None for row in distances for value in row):
        raise ProviderError("OSRM returned an incomplete road matrix.")
    if any(value is None for row in durations for value in row):
        raise ProviderError("OSRM returned an incomplete duration matrix.")
    return RoadMatrices(
        distance_km=np.asarray(distances, dtype=float) / 1000,
        duration_seconds=np.asarray(durations, dtype=float),
        provider="OSRM driving profile",
        snapped_names=[item.get("name", "") for item in payload.get("sources", [])],
    )


def fetch_osrm_route(
    route: Sequence[int],
    locations: Sequence[Location],
    base_url: str = DEFAULT_OSRM_URL,
    timeout: float = 25.0,
    session=requests,
) -> RoadRoute:
    ordered = [locations[index] for index in route]
    url = f"{base_url.rstrip('/')}/route/v1/driving/{_coordinates(ordered)}"
    try:
        response = session.get(
            url,
            params={"overview": "full", "geometries": "geojson", "steps": "false"},
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        item = payload["routes"][0]
        coordinates = [(float(lat), float(lon)) for lon, lat in item["geometry"]["coordinates"]]
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        raise ProviderError(f"OSRM route geometry request failed: {exc}") from exc
    return RoadRoute(
        coordinates=coordinates,
        distance_km=float(item["distance"]) / 1000,
        duration_minutes=float(item["duration"]) / 60,
    )


_geocode_lock = Lock()
_last_geocode_request = 0.0


@lru_cache(maxsize=512)
def geocode_address(
    query: str,
    base_url: str = DEFAULT_NOMINATIM_URL,
    timeout: float = 15.0,
) -> list[dict[str, object]]:
    global _last_geocode_request
    query = query.strip()
    if len(query) < 3:
        raise ProviderError("Enter at least three characters for address search.")
    with _geocode_lock:
        wait_for = 1.0 - (monotonic() - _last_geocode_request)
        if wait_for > 0:
            sleep(wait_for)
        try:
            response = requests.get(
                f"{base_url.rstrip('/')}/search",
                params={"q": query, "format": "jsonv2", "limit": 5, "addressdetails": 0},
                headers={"User-Agent": USER_AGENT},
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ProviderError(f"Geocoding failed: {exc}") from exc
        finally:
            _last_geocode_request = monotonic()
    return [
        {
            "display_name": item["display_name"],
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"]),
            "place_id": str(item.get("place_id", "")),
        }
        for item in payload
    ]


def fetch_tomtom_traffic_summary(
    route: Sequence[int],
    locations: Sequence[Location],
    api_key: str,
    timeout: float = 25.0,
    session=requests,
) -> TrafficSummary:
    if not api_key.strip():
        raise ProviderError("A TomTom API key is required for live traffic.")
    points = ":".join(
        f"{locations[index].latitude:.7f},{locations[index].longitude:.7f}" for index in route
    )
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{points}/json"
    try:
        response = session.get(
            url,
            params={
                "key": api_key.strip(),
                "traffic": "true",
                "computeTravelTimeFor": "all",
                "routeType": "fastest",
                "travelMode": "car",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        summary = payload["routes"][0]["summary"]
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        raise ProviderError(f"TomTom traffic request failed: {exc}") from exc
    return TrafficSummary(
        distance_km=float(summary["lengthInMeters"]) / 1000,
        travel_time_minutes=float(summary["travelTimeInSeconds"]) / 60,
        traffic_delay_minutes=(
            float(summary["trafficDelayInSeconds"]) / 60
            if summary.get("trafficDelayInSeconds") is not None
            else None
        ),
        no_traffic_minutes=(
            float(summary["noTrafficTravelTimeInSeconds"]) / 60
            if summary.get("noTrafficTravelTimeInSeconds") is not None
            else None
        ),
        departure_time=summary.get("departureTime"),
        arrival_time=summary.get("arrivalTime"),
    )
