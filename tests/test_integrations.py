import numpy as np
import pytest

from src.integrations import (
    ProviderError, fetch_osrm_matrix, fetch_osrm_route, fetch_tomtom_traffic_summary,
    geocode_address,
)
from src.models import Location


class FakeResponse:
    def __init__(self, payload, status=200, content=b""):
        self.payload = payload
        self.status = status
        self.content = content
        self.headers = {"content-type": "application/json"}

    def raise_for_status(self):
        if self.status >= 400:
            import requests
            raise requests.HTTPError(f"HTTP {self.status}")

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(self.payload)


def locations():
    return [Location("D", "Depot", 12.9, 77.6), Location("A", "Stop", 12.91, 77.61)]


def test_osrm_matrix_conversion_and_headers():
    session = FakeSession({
        "code": "Ok", "distances": [[0, 1500], [1400, 0]],
        "durations": [[0, 180], [170, 0]], "sources": [{"name": "D"}, {"name": "A"}],
    })
    result = fetch_osrm_matrix(locations(), session=session)
    assert result.distance_km[0, 1] == pytest.approx(1.5)
    assert result.duration_seconds[1, 0] == 170
    assert "User-Agent" in session.calls[0][1]["headers"]


def test_osrm_incomplete_matrix_rejected():
    session = FakeSession({"code": "Ok", "distances": [[0, None], [1, 0]], "durations": [[0, 1], [1, 0]]})
    with pytest.raises(ProviderError, match="incomplete"):
        fetch_osrm_matrix(locations(), session=session)


def test_osrm_route_geojson_conversion():
    session = FakeSession({
        "routes": [{"distance": 2200, "duration": 360, "geometry": {"coordinates": [[77.6, 12.9], [77.61, 12.91]]}}]
    })
    result = fetch_osrm_route([0, 1], locations(), session=session)
    assert result.coordinates == [(12.9, 77.6), (12.91, 77.61)]
    assert result.duration_minutes == 6


def test_tomtom_traffic_summary():
    session = FakeSession({"routes": [{"summary": {
        "lengthInMeters": 9000, "travelTimeInSeconds": 1200,
        "trafficDelayInSeconds": 180, "noTrafficTravelTimeInSeconds": 1020,
        "departureTime": "2026-01-01T10:00:00Z", "arrivalTime": "2026-01-01T10:20:00Z",
    }}]})
    result = fetch_tomtom_traffic_summary([0, 1], locations(), "key", session=session)
    assert result.distance_km == 9
    assert result.traffic_delay_minutes == 3


def test_tomtom_requires_key():
    with pytest.raises(ProviderError, match="key"):
        fetch_tomtom_traffic_summary([0, 1], locations(), "")


def test_explicit_geocoding_converts_coordinates(monkeypatch):
    import src.integrations as integrations

    integrations._last_geocode_request = 0
    geocode_address.cache_clear()
    monkeypatch.setattr(integrations.requests, "get", lambda *args, **kwargs: FakeResponse([
        {"display_name": "Test Place", "lat": "12.95", "lon": "77.62", "place_id": 7}
    ]))
    result = geocode_address("Test Place")
    assert result[0]["latitude"] == 12.95
    assert result[0]["place_id"] == "7"
