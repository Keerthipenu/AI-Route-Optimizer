from __future__ import annotations

from itertools import permutations
from math import factorial
from time import perf_counter

import numpy as np

from ..models import AlgorithmResult, RouteConstraints
from ..objectives import RouteObjective
from ..route_utils import route_distance, validate_route


def brute_force(
    matrix: np.ndarray,
    constraints: RouteConstraints | None = None,
    max_destinations: int = 9,
    objective: RouteObjective | None = None,
) -> AlgorithmResult:
    constraints = constraints or RouteConstraints()
    objective = objective or RouteObjective()
    size = len(matrix)
    if size == 0:
        raise ValueError("Cannot optimize an empty distance matrix.")
    destination_count = size - 1
    if destination_count > max_destinations:
        raise ValueError(
            f"Brute Force is limited to {max_destinations} destinations; received {destination_count}. "
            "Use a heuristic for larger instances."
        )
    middle = [i for i in range(size) if i not in {constraints.depot_index, constraints.end_index}]
    started = perf_counter()
    best_route: list[int] | None = None
    best_score = float("inf")
    ties = 0
    evaluated = 0
    for order in permutations(middle):
        candidate = [constraints.depot_index, *order]
        if constraints.end_index is not None:
            candidate.append(constraints.end_index)
        elif constraints.round_trip:
            candidate.append(constraints.depot_index)
        score = objective.score(candidate, matrix)
        evaluated += 1
        if score < best_score - 1e-12:
            best_route, best_score, ties = candidate, score, 1
        elif abs(score - best_score) <= 1e-12:
            ties += 1
            if best_route is None or tuple(candidate) < tuple(best_route):
                best_route = candidate
    if best_route is None:  # only possible for malformed input; factorial(0) still yields one route
        best_route = [constraints.depot_index]
    validate_route(best_route, size, constraints)
    return AlgorithmResult(
        algorithm="Brute Force",
        route=best_route,
        total_distance=route_distance(best_route, matrix),
        runtime_seconds=perf_counter() - started,
        work_count=evaluated,
        work_label="permutations evaluated",
        metadata={
            "guarantees_optimal": True,
            "optimal_tie_count": ties,
            "search_space": factorial(len(middle)),
            "objective": objective.label,
            "objective_score": best_score if best_score != float("inf") else 0.0,
        },
    )
