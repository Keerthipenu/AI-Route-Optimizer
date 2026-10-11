import numpy as np
import pytest

from src.distance import build_distance_matrix, haversine_km
from src.models import Location


def test_haversine_known_equatorial_degree():
    assert haversine_km(0, 0, 0, 1) == pytest.approx(111.195, rel=1e-4)


def test_distance_symmetry_and_zero_diagonal(square_locations):
    matrix = build_distance_matrix(square_locations)
    assert np.allclose(matrix, matrix.T)
    assert np.allclose(np.diag(matrix), 0)


def test_distance_matrix_correctness(square_locations):
    matrix = build_distance_matrix(square_locations)
    assert matrix.shape == (4, 4)
    assert matrix[0, 1] == pytest.approx(haversine_km(0, 0, 0, 1))


def test_duplicate_coordinates_are_zero_distance():
    items = [Location("A", "A", 12.0, 77.0), Location("B", "B", 12.0, 77.0)]
    matrix = build_distance_matrix(items)
    assert matrix[0, 1] == 0


@pytest.mark.parametrize("args", [(91, 0, 0, 0), (0, 181, 0, 0), (float("nan"), 0, 0, 0)])
def test_invalid_coordinates(args):
    with pytest.raises(ValueError):
        haversine_km(*args)
