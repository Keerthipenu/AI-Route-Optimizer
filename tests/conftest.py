import numpy as np
import pytest

from src.models import Location


@pytest.fixture
def square_locations():
    return [
        Location("D", "Depot", 0.0, 0.0),
        Location("A", "A", 0.0, 1.0),
        Location("B", "B", 1.0, 1.0),
        Location("C", "C", 1.0, 0.0),
    ]


@pytest.fixture
def square_matrix():
    return np.array([
        [0.0, 1.0, 2**0.5, 1.0],
        [1.0, 0.0, 1.0, 2**0.5],
        [2**0.5, 1.0, 0.0, 1.0],
        [1.0, 2**0.5, 1.0, 0.0],
    ])
