import json

import pytest

from src.algorithms import nearest_neighbor
from src.evaluation import evaluate_algorithms, improvement_percent, optimality_gap, repeated_annealing
from src.export_utils import result_to_json, route_to_frame
from src.models import RouteConstraints


def test_metric_formulas_and_zero_edges():
    assert improvement_percent(10, 8) == pytest.approx(20)
    assert improvement_percent(0, 0) == 0
    assert optimality_gap(11, 10) == pytest.approx(10)
    assert optimality_gap(0, 0) == 0
    assert optimality_gap(1, 0) == float("inf")
    assert optimality_gap(1, None) is None


def test_evaluation_uses_exact_result_as_benchmark(square_matrix):
    report = evaluate_algorithms(square_matrix, sa_iterations=300, brute_force_limit=5)
    brute = report.table.loc[report.table["Algorithm"] == "Brute Force"].iloc[0]
    assert brute["Optimality gap (%)"] == pytest.approx(0)
    assert report.metadata["exact_optimum_available"] is True


def test_evaluation_refuses_brute_force_only_when_over_limit():
    import numpy as np

    with pytest.raises(ValueError, match="disabled"):
        evaluate_algorithms(np.zeros((8, 8)), algorithms=["Brute Force"], brute_force_limit=5)


def test_repeated_annealing_is_consistent(square_matrix):
    first = repeated_annealing(square_matrix, RouteConstraints(), [1, 2], iterations=100)
    second = repeated_annealing(square_matrix, RouteConstraints(), [1, 2], iterations=100)
    assert first["distance_km"].tolist() == second["distance_km"].tolist()


def test_exported_route_correctness(square_matrix, square_locations):
    result = nearest_neighbor(square_matrix)
    frame = route_to_frame(result, square_locations, square_matrix)
    assert frame.iloc[0]["location_id"] == "D"
    assert frame.iloc[-1]["location_id"] == "D"
    assert frame.iloc[-1]["cumulative_distance_km"] == pytest.approx(result.total_distance)
    payload = json.loads(result_to_json(result, square_locations, square_matrix))
    assert len(payload["stops"]) == len(result.route)
