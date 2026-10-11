import pandas as pd
import pytest

from src.models import Location
from src.tracking import fetch_telemetry_feed, tracking_snapshot, validate_telemetry


def test_tracking_uses_latest_vehicle_position():
    frame = pd.DataFrame([
        {"timestamp": "2026-01-01T10:00:00Z", "vehicle_id": "V1", "latitude": 0.0, "longitude": 0.0},
        {"timestamp": "2026-01-01T10:05:00Z", "vehicle_id": "V1", "latitude": 0.0, "longitude": 1.0},
    ])
    locations = [Location("D", "Depot", 0, 0), Location("A", "Stop", 0, 1)]
    snapshot = tracking_snapshot(frame, [0, 1, 0], locations)
    assert snapshot.iloc[0]["nearest_route_stop"] == "Stop"
    assert bool(snapshot.iloc[0]["at_stop"]) is True


def test_tracking_rejects_malformed_feed():
    with pytest.raises(ValueError, match="Missing"):
        validate_telemetry(pd.DataFrame({"vehicle_id": ["V1"]}))


def test_http_json_tracking_feed():
    class Response:
        headers = {"content-type": "application/json"}
        content = b""
        def raise_for_status(self):
            return None
        def json(self):
            return {"positions": [{
                "timestamp": "2026-01-01T10:00:00Z", "vehicle_id": "V1",
                "latitude": 12.9, "longitude": 77.6,
            }]}
    class Session:
        @staticmethod
        def get(*args, **kwargs):
            return Response()

    result = fetch_telemetry_feed("https://fleet.example/positions", session=Session)
    assert result.iloc[0]["vehicle_id"] == "V1"
