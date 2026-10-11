from __future__ import annotations

from math import exp
from random import Random
from time import perf_counter

import numpy as np

from ..models import AlgorithmResult, RouteConstraints
from ..objectives import RouteObjective
from ..route_utils import movable_positions, route_distance, validate_route
from .nearest_neighbor import nearest_neighbor


def simulated_annealing(
    matrix: np.ndarray,
    constraints: RouteConstraints | None = None,
    initial_route: list[int] | None = None,
    initial_temperature: float = 100.0,
    cooling_rate: float = 0.995,
    iterations: int = 5_000,
    seed: int = 42,
    objective: RouteObjective | None = None,
) -> AlgorithmResult:
    if initial_temperature <= 0:
        raise ValueError("Initial temperature must be positive.")
    if not 0 < cooling_rate < 1:
        raise ValueError("Cooling rate must be between 0 and 1.")
    if iterations < 0:
        raise ValueError("Iterations cannot be negative.")
    constraints = constraints or RouteConstraints()
    objective = objective or RouteObjective()
    started = perf_counter()
    if len(matrix) == 0:
        raise ValueError("Cannot optimize an empty distance matrix.")
    rng = Random(seed)
    current_route = list(initial_route or nearest_neighbor(matrix, constraints, objective).route)
    validate_route(current_route, len(matrix), constraints)
    initial_distance = route_distance(current_route, matrix)
    current_score = best_score = objective.score(current_route, matrix)
    best_distance = initial_distance
    best_route = current_route.copy()
    temperature = float(initial_temperature)
    history: list[dict[str, object]] = []
    accepted = 0
    movable = movable_positions(current_route, constraints)
    completed = 0
    for step in range(iterations):
        if len(movable) < 2:
            break
        i, j = sorted(rng.sample(movable, 2))
        candidate = current_route[:i] + list(reversed(current_route[i : j + 1])) + current_route[j + 1 :]
        candidate_score = objective.score(candidate, matrix)
        delta = candidate_score - current_score
        was_accepted = delta <= 0 or rng.random() < exp(-delta / temperature)
        if was_accepted:
            current_route, current_score = candidate, candidate_score
            accepted += 1
            if current_score < best_score - 1e-12:
                best_route, best_score = current_route.copy(), current_score
                best_distance = route_distance(best_route, matrix)
        if step == 0 or (step + 1) % max(1, iterations // 250) == 0 or step == iterations - 1:
            history.append({
                "iteration": step + 1,
                "best_distance": best_distance,
                "current_distance": route_distance(current_route, matrix),
                "best_score": best_score,
                "temperature": temperature,
                "accepted": was_accepted,
            })
        temperature *= cooling_rate
        completed = step + 1
    validate_route(best_route, len(matrix), constraints)
    return AlgorithmResult(
        algorithm="Simulated Annealing",
        route=best_route,
        total_distance=best_distance,
        runtime_seconds=perf_counter() - started,
        work_count=completed,
        work_label="neighbor proposals",
        metadata={
            "initial_distance": initial_distance,
            "iterations": completed,
            "accepted_moves": accepted,
            "final_temperature": temperature,
            "seed": seed,
            "guarantees_optimal": False,
            "objective": objective.label,
            "objective_score": best_score,
        },
        history=history,
    )
