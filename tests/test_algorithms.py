import numpy as np
import pytest

from src.algorithms import brute_force, nearest_neighbor, simulated_annealing, two_opt
from src.models import RouteConstraints
from src.route_utils import route_distance, validate_route


@pytest.mark.parametrize("solver", [nearest_neighbor, brute_force, two_opt, simulated_annealing])
def test_round_trip_route_validity(square_matrix, solver):
    kwargs = {"iterations": 500, "seed": 9} if solver is simulated_annealing else {}
    result = solver(square_matrix, RouteConstraints(), **kwargs)
    validate_route(result.route, 4, RouteConstraints())
    assert result.route[0] == result.route[-1] == 0


def test_brute_force_finds_square_optimum(square_matrix):
    result = brute_force(square_matrix)
    assert result.total_distance == pytest.approx(4.0)
    assert result.work_count == 6
    assert result.metadata["optimal_tie_count"] == 2


def test_two_opt_never_worsens_initial_route(square_matrix):
    poor_route = [0, 2, 1, 3, 0]
    result = two_opt(square_matrix, initial_route=poor_route)
    assert result.total_distance <= route_distance(poor_route, square_matrix)
    validate_route(result.route, 4, RouteConstraints())


def test_simulated_annealing_seed_reproducibility(square_matrix):
    a = simulated_annealing(square_matrix, iterations=1_000, seed=123)
    b = simulated_annealing(square_matrix, iterations=1_000, seed=123)
    assert a.route == b.route
    assert a.total_distance == b.total_distance
    assert a.history == b.history


def test_brute_force_refuses_large_instance():
    matrix = np.zeros((7, 7))
    with pytest.raises(ValueError, match="limited"):
        brute_force(matrix, max_destinations=5)
