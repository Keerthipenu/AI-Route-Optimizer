from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Location:
    location_id: str
    name: str
    latitude: float
    longitude: float
    priority: int | None = None
    service_duration: float | None = None


@dataclass(frozen=True, slots=True)
class RouteConstraints:
    depot_index: int = 0
    round_trip: bool = True
    end_index: int | None = None

    def __post_init__(self) -> None:
        if self.round_trip and self.end_index is not None:
            raise ValueError("A round trip cannot have a separate fixed endpoint.")
        if self.end_index == self.depot_index:
            raise ValueError("The one-way endpoint must differ from the depot.")


@dataclass(slots=True)
class AlgorithmResult:
    algorithm: str
    route: list[int]
    total_distance: float
    runtime_seconds: float
    work_count: int = 0
    work_label: str = "operations"
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def as_record(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "route": " -> ".join(map(str, self.route)),
            "distance_km": self.total_distance,
            "runtime_ms": self.runtime_seconds * 1000,
            "work_count": self.work_count,
            "work_label": self.work_label,
            **self.metadata,
        }
