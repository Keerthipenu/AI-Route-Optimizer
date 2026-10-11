import numpy as np
import pytest

from src.algorithms import brute_force, nearest_neighbor, simulated_annealing, two_opt
from src.models import RouteConstraints
from src.route_utils import validate_route


@pytest.mark.parametrize("solver", [nearest_neighbor, brute_force, two_opt, simulated_annealing])
def test_one_way_fixed_endpoint(square_matrix, solver):
    constraints = RouteConstraints(round_trip=False, end_index=2)
    kwargs = {"iterations": 300, "seed": 2} if solver is simulated_annealing else {}
    result = solver(square_matrix, constraints, **kwargs)
    validate_route(result.route, 4, constraints)
    assert result.route[0] == 0
    assert result.route[-1] == 2


@pytest.mark.parametrize("round_trip,expected", [(True, [0, 0]), (False, [0])])
def test_single_location(round_trip, expected):
    matrix = np.zeros((1, 1))
    constraints = RouteConstraints(round_trip=round_trip)
    for solver in (nearest_neighbor, brute_force, two_opt):
        assert solver(matrix, constraints).route == expected
    assert simulated_annealing(matrix, constraints, iterations=20).route == expected


def test_invalid_route_is_detected(square_matrix):
    with pytest.raises(ValueError, match="exactly once"):
        validate_route([0, 1, 1, 3, 0], 4, RouteConstraints())
