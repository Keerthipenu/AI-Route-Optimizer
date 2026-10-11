import numpy as np

from src.models import Location
from src.objectives import RouteObjective, total_route_minutes


def test_priority_weighted_objective_rewards_urgent_stop_earlier():
    locations = [
        Location("D", "Depot", 0, 0, priority=3),
        Location("H", "High", 0, 0, priority=1),
        Location("L", "Low", 0, 0, priority=3),
    ]
    matrix = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
    objective = RouteObjective("priority_weighted_eta", locations=locations, assumed_speed_kph=60)
    assert objective.score([0, 1, 2, 0], matrix) < objective.score([0, 2, 1, 0], matrix)


def test_eta_includes_service_duration():
    locations = [Location("D", "Depot", 0, 0), Location("A", "Stop", 0, 0, service_duration=15)]
    matrix = np.array([[0, 35], [35, 0]], dtype=float)
    assert total_route_minutes([0, 1, 0], matrix, locations, assumed_speed_kph=35) == 135


def test_duration_matrix_overrides_speed_assumption():
    locations = [Location("D", "Depot", 0, 0), Location("A", "Stop", 0, 0)]
    matrix = np.array([[0, 999], [999, 0]], dtype=float)
    duration = np.array([[0, 300], [300, 0]], dtype=float)
    assert total_route_minutes([0, 1, 0], matrix, locations, duration) == 10
