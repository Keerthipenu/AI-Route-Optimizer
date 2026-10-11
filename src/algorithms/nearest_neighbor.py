from __future__ import annotations

from time import perf_counter

import numpy as np

from ..models import AlgorithmResult, RouteConstraints
from ..objectives import RouteObjective
from ..route_utils import route_distance, validate_route


def nearest_neighbor(
    matrix: np.ndarray,
    constraints: RouteConstraints | None = None,
    objective: RouteObjective | None = None,
) -> AlgorithmResult:
    constraints = constraints or RouteConstraints()
    objective = objective or RouteObjective()
    started = perf_counter()
    size = len(matrix)
    if size == 0:
        raise ValueError("Cannot optimize an empty distance matrix.")
    remaining = set(range(size)) - {constraints.depot_index}
    if constraints.end_index is not None:
        remaining.discard(constraints.end_index)
    route = [constraints.depot_index]
    comparisons = 0
    steps: list[dict[str, object]] = []
    while remaining:
        current = route[-1]
        comparisons += len(remaining)
        next_index = min(
            remaining,
            key=lambda candidate: (objective.greedy_candidate_score(current, candidate, matrix), candidate),
        )
        steps.append({
            "current": current,
            "unvisited": sorted(remaining),
            "selected": next_index,
            "leg_distance": float(matrix[current, next_index]),
        })
        route.append(next_index)
        remaining.remove(next_index)
    if constraints.end_index is not None:
        route.append(constraints.end_index)
        comparisons += 1
    elif constraints.round_trip:
        route.append(constraints.depot_index)
        comparisons += 1
    validate_route(route, size, constraints)
    return AlgorithmResult(
        algorithm="Nearest Neighbor",
        route=route,
        total_distance=route_distance(route, matrix),
        runtime_seconds=perf_counter() - started,
        work_count=comparisons,
        work_label="distance comparisons",
        metadata={
            "guarantees_optimal": False,
            "objective": objective.label,
            "objective_score": objective.score(route, matrix),
        },
        history=steps,
    )
