"""Atribuição gulosa de entregas e particionamento em tokens de capacidade."""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from traveling_salesman_problem.problem.vrp_models import (
    Coordinate,
    DeliveryPoint,
    DeliveryToken,
)


def _euclidean(point_a: Coordinate, point_b: Coordinate) -> float:
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


def split_into_tokens(point: DeliveryPoint, capacity: int) -> List[DeliveryToken]:
    if capacity < 1:
        raise ValueError("capacity must be >= 1")
    if point.demand < 1:
        raise ValueError("demand must be >= 1")

    remaining = point.demand
    tokens: List[DeliveryToken] = []
    while remaining > 0:
        quantity = min(capacity, remaining)
        tokens.append(
            DeliveryToken(
                point_id=point.id,
                quantity=quantity,
                priority=point.priority,
            )
        )
        remaining -= quantity
    return tokens


def assign_deliveries_greedy(
    deliveries: List[DeliveryPoint],
    vehicle_count: int,
    depot: Coordinate,
) -> Dict[int, List[DeliveryPoint]]:
    if vehicle_count < 1:
        raise ValueError("vehicle_count must be >= 1")

    assignment: Dict[int, List[DeliveryPoint]] = {
        vehicle_id: [] for vehicle_id in range(vehicle_count)
    }
    loads: Dict[int, int] = {vehicle_id: 0 for vehicle_id in range(vehicle_count)}

    ordered = sorted(
        deliveries,
        key=lambda point: (
            _euclidean(depot, point.coordinate),
            point.id,
        ),
    )

    for point in ordered:
        best_vehicle = min(
            range(vehicle_count),
            key=lambda vehicle_id: (loads[vehicle_id], vehicle_id),
        )
        assignment[best_vehicle].append(point)
        loads[best_vehicle] += point.demand

    return assignment
