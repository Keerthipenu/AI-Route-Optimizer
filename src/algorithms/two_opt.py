from __future__ import annotations

from time import perf_counter

import numpy as np

from ..models import AlgorithmResult, RouteConstraints
from ..objectives import RouteObjective
from ..route_utils import movable_positions, route_distance, validate_route
from .nearest_neighbor import nearest_neighbor


def two_opt(
    matrix: np.ndarray,
    constraints: RouteConstraints | None = None,
    initial_route: list[int] | None = None,
    max_iterations: int = 250,
    objective: RouteObjective | None = None,
) -> AlgorithmResult:
    constraints = constraints or RouteConstraints()
    objective = objective or RouteObjective()
    started = perf_counter()
    if len(matrix) == 0:
        raise ValueError("Cannot optimize an empty distance matrix.")
    route = list(initial_route or nearest_neighbor(matrix, constraints, objective).route)
    validate_route(route, len(matrix), constraints)
    initial = route_distance(route, matrix)
    current_score = objective.score(route, matrix)
    initial_score = current_score
    accepted: list[dict[str, object]] = []
    candidates = 0
    iterations = 0
    positions = movable_positions(route, constraints)
    while iterations < max_iterations and len(positions) >= 2:
        iterations += 1
        best_score = current_score
        best_candidate: list[int] | None = None
        best_pair: tuple[int, int] | None = None
        for offset, i in enumerate(positions[:-1]):
            for j in positions[offset + 1 :]:
                candidate = route[:i] + list(reversed(route[i : j + 1])) + route[j + 1 :]
                score = objective.score(candidate, matrix)
                candidates += 1
                if score < best_score - 1e-12:
                    best_score, best_candidate, best_pair = score, candidate, (i, j)
        if best_candidate is None:
            break
        accepted.append({
            "iteration": iterations,
            "positions": best_pair,
            "before_score": current_score,
            "after_score": best_score,
            "distance_km": route_distance(best_candidate, matrix),
            "route": best_candidate.copy(),
        })
        route, current_score = best_candidate, best_score
    validate_route(route, len(matrix), constraints)
    final_distance = route_distance(route, matrix)
    return AlgorithmResult(
        algorithm="2-opt",
        route=route,
        total_distance=final_distance,
        runtime_seconds=perf_counter() - started,
        work_count=candidates,
        work_label="candidate reversals",
        metadata={
            "initial_distance": initial,
            "improvement_km": initial - final_distance,
            "objective": objective.label,
            "initial_objective_score": initial_score,
            "objective_score": current_score,
            "accepted_swaps": len(accepted),
            "iterations": iterations,
            "guarantees_optimal": False,
        },
        history=accepted,
    )
