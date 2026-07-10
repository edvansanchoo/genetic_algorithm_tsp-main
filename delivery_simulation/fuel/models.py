"""Tipos e constantes de combustível / postos."""

from dataclasses import dataclass, field
from typing import List, Tuple

Coordinate = Tuple[float, float]

MAX_FUEL = 30.0
INITIAL_FUEL = 30.0
MAX_STATION_DISTANCE_FROM_NETWORK = 100.0
FUEL_STATION_ID_PREFIX = "F"
MIN_STATION_SEPARATION = 30.0


@dataclass(frozen=True)
class GasStation:
    id: str
    coordinate: Coordinate


@dataclass
class FuelLeg:
    leg_index: int
    from_node_id: str
    to_node_id: str
    distance: float
    fuel_before: float
    fuel_consumed: float
    fuel_after: float


@dataclass
class FuelStopEvent:
    station_id: str
    fuel_on_arrival: float
    fuel_on_departure: float


@dataclass
class RouteFuelReport:
    legs: List[FuelLeg] = field(default_factory=list)
    stops: List[FuelStopEvent] = field(default_factory=list)
    final_fuel: float = INITIAL_FUEL
    is_feasible: bool = True
    expanded_node_ids: List[str] = field(default_factory=list)
    total_distance: float = 0.0
