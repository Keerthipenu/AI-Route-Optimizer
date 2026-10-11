from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import numpy as np
import pandas as pd

from .algorithms import brute_force, nearest_neighbor, simulated_annealing, two_opt
from .models import AlgorithmResult, RouteConstraints
from .objectives import RouteObjective


def improvement_percent(initial: float, optimized: float) -> float:
    if initial == 0:
        return 0.0
    return (initial - optimized) / initial * 100


def optimality_gap(distance: float, optimum: float | None) -> float | None:
    if optimum is None:
        return None
    if optimum == 0:
        return 0.0 if distance == 0 else float("inf")
    return (distance - optimum) / optimum * 100


@dataclass(slots=True)
class EvaluationReport:
    results: list[AlgorithmResult]
    table: pd.DataFrame
    metadata: dict[str, object]


def evaluate_algorithms(
    matrix: np.ndarray,
    constraints: RouteConstraints | None = None,
    algorithms: Iterable[str] = ("Nearest Neighbor", "2-opt", "Simulated Annealing", "Brute Force"),
    seed: int = 42,
    sa_iterations: int = 5_000,
    brute_force_limit: int = 9,
    objective: RouteObjective | None = None,
) -> EvaluationReport:
    constraints = constraints or RouteConstraints()
    objective = objective or RouteObjective()
    requested = list(algorithms)
    baseline = nearest_neighbor(matrix, constraints, objective)
    results: list[AlgorithmResult] = []
    if "Nearest Neighbor" in requested:
        results.append(baseline)
    if "2-opt" in requested:
        results.append(two_opt(matrix, constraints, initial_route=baseline.route, objective=objective))
    if "Simulated Annealing" in requested:
        results.append(simulated_annealing(
            matrix, constraints, initial_route=baseline.route, iterations=sa_iterations, seed=seed,
            objective=objective,
        ))
    destination_count = len(matrix) - 1
    if "Brute Force" in requested and destination_count <= brute_force_limit:
        results.append(brute_force(
            matrix, constraints, max_destinations=brute_force_limit, objective=objective
        ))
    elif requested == ["Brute Force"]:
        raise ValueError(
            f"Brute Force is disabled for {destination_count} destinations because the safety limit is "
            f"{brute_force_limit}. Choose a heuristic or raise the limit only for a small instance."
        )
    optimum = next((r.metadata.get("objective_score") for r in results if r.algorithm == "Brute Force"), None)
    baseline_score = float(baseline.metadata.get("objective_score", baseline.total_distance))
    rows = []
    for result in results:
        rows.append({
            "Algorithm": result.algorithm,
            "Distance (km)": result.total_distance,
            "Objective": result.metadata.get("objective", "distance_km"),
            "Objective score": result.metadata.get("objective_score", result.total_distance),
            "Runtime (ms)": result.runtime_seconds * 1000,
            "Improvement vs NN (%)": improvement_percent(
                baseline_score, float(result.metadata.get("objective_score", result.total_distance))
            ),
            "Optimality gap (%)": optimality_gap(
                float(result.metadata.get("objective_score", result.total_distance)), optimum
            ),
            "Work": result.work_count,
            "Work metric": result.work_label,
        })
    return EvaluationReport(
        results=results,
        table=pd.DataFrame(rows),
        metadata={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "seed": seed,
            "sa_iterations": sa_iterations,
            "brute_force_limit": brute_force_limit,
            "exact_optimum_available": optimum is not None,
            "objective": objective.label,
        },
    )


def repeated_annealing(
    matrix: np.ndarray,
    constraints: RouteConstraints,
    seeds: Iterable[int],
    iterations: int = 5_000,
    objective: RouteObjective | None = None,
) -> pd.DataFrame:
    rows = []
    for seed in seeds:
        result = simulated_annealing(
            matrix, constraints, iterations=iterations, seed=seed, objective=objective
        )
        rows.append({
            "seed": seed,
            "distance_km": result.total_distance,
            "objective_score": result.metadata.get("objective_score", result.total_distance),
            "runtime_ms": result.runtime_seconds * 1000,
        })
    return pd.DataFrame(rows)
