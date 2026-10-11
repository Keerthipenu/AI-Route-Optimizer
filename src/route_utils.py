from __future__ import annotations

from collections import Counter
from typing import Sequence

import numpy as np

from .models import RouteConstraints


def route_distance(route: Sequence[int], matrix: np.ndarray) -> float:
    if len(route) < 2:
        return 0.0
    return float(sum(matrix[a, b] for a, b in zip(route, route[1:])))


def expected_route_length(size: int, constraints: RouteConstraints) -> int:
    return size + 1 if constraints.round_trip else size


def validate_route(route: Sequence[int], size: int, constraints: RouteConstraints) -> None:
    if size < 1:
        raise ValueError("At least one location is required.")
    if constraints.depot_index not in range(size):
        raise ValueError("Depot index is outside the distance matrix.")
    if constraints.end_index is not None and constraints.end_index not in range(size):
        raise ValueError("Endpoint index is outside the distance matrix.")
    if not route or route[0] != constraints.depot_index:
        raise ValueError("Every route must start at the depot.")
    if constraints.round_trip:
        if len(route) != size + 1 or route[-1] != constraints.depot_index:
            raise ValueError("A round trip must end at the depot.")
        body = route[:-1]
    else:
        if len(route) != size:
            raise ValueError("A one-way route must visit every location once.")
        if constraints.end_index is not None and route[-1] != constraints.end_index:
            raise ValueError("The route does not end at the fixed endpoint.")
        body = route
    counts = Counter(body)
    if set(body) != set(range(size)) or any(count != 1 for count in counts.values()):
        raise ValueError("The route must visit every location exactly once.")


def movable_positions(route: Sequence[int], constraints: RouteConstraints) -> list[int]:
    stop = len(route) - 1 if constraints.round_trip or constraints.end_index is not None else len(route)
    return list(range(1, stop))
