"""Modelos de domínio do VRP hospitalar (Camada 2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

Coordinate = Tuple[float, float]

DEPOT_ID = "DEPOT"


@dataclass(frozen=True)
class DeliveryPoint:
    id: str
    coordinate: Coordinate
    priority: int
    demand: int


@dataclass(frozen=True)
class DeliveryToken:
    point_id: str
    quantity: int
    priority: int


@dataclass
class TripStop:
    node_id: str
    quantity: int
    coordinate: Coordinate


@dataclass
class Trip:
    stops: list[TripStop]
    distance: float
    path_node_ids: list[list[str]]
