from __future__ import annotations

import json
from typing import Sequence

import pandas as pd

from .models import AlgorithmResult, Location


def route_to_frame(result: AlgorithmResult, locations: Sequence[Location], matrix) -> pd.DataFrame:
    rows = []
    cumulative = 0.0
    for stop_number, index in enumerate(result.route):
        leg = 0.0 if stop_number == 0 else float(matrix[result.route[stop_number - 1], index])
        cumulative += leg
        location = locations[index]
        rows.append({
            "stop_number": stop_number,
            "location_id": location.location_id,
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "leg_distance_km": leg,
            "cumulative_distance_km": cumulative,
        })
    return pd.DataFrame(rows)


def route_to_csv(result: AlgorithmResult, locations: Sequence[Location], matrix) -> bytes:
    return route_to_frame(result, locations, matrix).to_csv(index=False).encode("utf-8")


def result_to_json(result: AlgorithmResult, locations: Sequence[Location], matrix) -> bytes:
    payload = {
        "summary": result.as_record(),
        "stops": route_to_frame(result, locations, matrix).to_dict(orient="records"),
    }
    return json.dumps(payload, indent=2).encode("utf-8")
