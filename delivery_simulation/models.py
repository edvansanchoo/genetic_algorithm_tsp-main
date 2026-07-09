"""Modelos de domínio do simulador de entregas."""

from dataclasses import dataclass, field
from typing import List, Tuple

Coordinate = Tuple[float, float]

MAX_CAPACITY = 10
VALID_TOTAL_ITEMS = (2, 4, 6, 8, 10, 12, 14)
DEPOT_ID = "DEPOT"
POINT_IDS = ("A", "B", "C")


@dataclass
class DeliveryPoint:
    id: str
    coordinate: Coordinate
    total_items: int
    remaining_items: int


@dataclass
class Stop:
    point_id: str
    items_delivered: int


@dataclass
class Trip:
    stops: List[Stop]
    distance: float


@dataclass
class Vehicle:
    id: int
    current_position: Coordinate
    current_load: int
    trips: List[Trip] = field(default_factory=list)
    assigned_points: List[str] = field(default_factory=list)


@dataclass
class SimulationConfig:
    vehicle_count: int
    delivery_point_count: int
    total_items: int


@dataclass
class SimulationResult:
    config: SimulationConfig
    depot: Coordinate
    delivery_points: List[DeliveryPoint]
    vehicles: List[Vehicle]
    total_system_distance: float
