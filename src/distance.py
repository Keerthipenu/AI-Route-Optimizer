from __future__ import annotations

from functools import lru_cache
from math import asin, cos, isfinite, radians, sin, sqrt
from typing import Iterable

import numpy as np

from .models import Location

EARTH_RADIUS_KM = 6371.0088


def validate_coordinate(latitude: float, longitude: float) -> None:
    if not (isfinite(latitude) and isfinite(longitude)):
        raise ValueError("Coordinates must be finite numbers.")
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180 degrees.")


@lru_cache(maxsize=16_384)
def _haversine_cached(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(min(1.0, a)))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    values = tuple(float(v) for v in (lat1, lon1, lat2, lon2))
    validate_coordinate(values[0], values[1])
    validate_coordinate(values[2], values[3])
    if values[:2] == values[2:]:
        return 0.0
    return _haversine_cached(*values)


def build_distance_matrix(locations: Iterable[Location]) -> np.ndarray:
    items = list(locations)
    matrix = np.zeros((len(items), len(items)), dtype=float)
    for i, source in enumerate(items):
        validate_coordinate(source.latitude, source.longitude)
        for j in range(i + 1, len(items)):
            target = items[j]
            distance = haversine_km(
                source.latitude, source.longitude, target.latitude, target.longitude
            )
            matrix[i, j] = matrix[j, i] = distance
    return matrix
