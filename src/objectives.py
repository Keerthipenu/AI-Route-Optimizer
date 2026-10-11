from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .models import Location
from .route_utils import route_distance


@dataclass(frozen=True, slots=True)
class RouteObjective:
    """Scores complete routes while distance remains separately reportable."""

    mode: str = "distance"
    duration_matrix: np.ndarray | None = None
    locations: Sequence[Location] | None = None
    assumed_speed_kph: float = 35.0

    @property
    def label(self) -> str:
        return "distance_km" if self.mode == "distance" else (
            "travel_minutes" if self.mode == "fastest" else "priority_weighted_arrival_minutes"
        )

    def travel_seconds(self, source: int, target: int, distance_matrix: np.ndarray) -> float:
        if self.duration_matrix is not None:
            return float(self.duration_matrix[source, target])
        if self.assumed_speed_kph <= 0:
            raise ValueError("Assumed speed must be positive.")
        return float(distance_matrix[source, target]) / self.assumed_speed_kph * 3600

    def score(self, route: Sequence[int], distance_matrix: np.ndarray) -> float:
        if self.mode == "distance":
            return route_distance(route, distance_matrix)
        elapsed_seconds = 0.0
        total = 0.0
        max_priority = max(
            (location.priority or 1 for location in self.locations or []), default=1
        )
        for position, (source, target) in enumerate(zip(route, route[1:]), start=1):
            elapsed_seconds += self.travel_seconds(source, target, distance_matrix)
            if self.mode == "priority_weighted_eta" and (not route or target != route[0] or position < len(route) - 1):
                location = self.locations[target] if self.locations else None
                priority = (location.priority if location else None) or max_priority
                weight = max_priority - priority + 1
                total += elapsed_seconds / 60 * weight
            service_minutes = (
                (self.locations[target].service_duration or 0.0)
                if self.locations and target < len(self.locations)
                else 0.0
            )
            elapsed_seconds += service_minutes * 60
        return elapsed_seconds / 60 if self.mode == "fastest" else total

    def greedy_candidate_score(
        self, current: int, candidate: int, distance_matrix: np.ndarray
    ) -> float:
        if self.mode == "distance":
            return float(distance_matrix[current, candidate])
        travel_minutes = self.travel_seconds(current, candidate, distance_matrix) / 60
        if self.mode == "fastest":
            return travel_minutes
        max_priority = max(
            (location.priority or 1 for location in self.locations or []), default=1
        )
        priority = (
            self.locations[candidate].priority or max_priority
            if self.locations
            else max_priority
        )
        weight = max_priority - priority + 1
        return travel_minutes / weight


def total_route_minutes(
    route: Sequence[int],
    distance_matrix: np.ndarray,
    locations: Sequence[Location],
    duration_matrix: np.ndarray | None = None,
    assumed_speed_kph: float = 35.0,
) -> float:
    return RouteObjective(
        mode="fastest",
        duration_matrix=duration_matrix,
        locations=locations,
        assumed_speed_kph=assumed_speed_kph,
    ).score(route, distance_matrix)
