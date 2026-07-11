"""Hit-test de nós no mapa para bloqueio manual."""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from traveling_salesman_problem.problem.delivery_mesh import DeliveryMesh
from traveling_salesman_problem.problem.road_network import Coordinate
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryPoint

ScreenPos = Tuple[int, int]


def _distance(screen_pos: ScreenPos, coordinate: Coordinate) -> float:
    return math.hypot(screen_pos[0] - coordinate[0], screen_pos[1] - coordinate[1])


def _nearest_within(
    screen_pos: ScreenPos,
    candidates: Sequence[Tuple[str, Coordinate]],
    hit_radius: float,
) -> Optional[str]:
    best_id: Optional[str] = None
    best_distance = hit_radius
    for node_id, coordinate in candidates:
        distance = _distance(screen_pos, coordinate)
        if distance <= best_distance:
            best_distance = distance
            best_id = node_id
    return best_id


def hit_test_map_node(
    mesh: Optional[DeliveryMesh],
    depot: Optional[Coordinate],
    deliveries: Sequence[DeliveryPoint],
    screen_pos: ScreenPos,
    hit_radius: float,
) -> Optional[str]:
    if mesh is None:
        return None

    blocked_candidates: List[Tuple[str, Coordinate]] = [
        (node_id, coordinate)
        for node_id, coordinate in mesh.blocked_coordinates.items()
    ]
    hit = _nearest_within(screen_pos, blocked_candidates, hit_radius)
    if hit is not None:
        return hit

    if depot is not None:
        hit = _nearest_within(screen_pos, [(DEPOT_ID, depot)], hit_radius)
        if hit is not None:
            return hit

    delivery_candidates = [
        (point.id, point.coordinate) for point in deliveries
    ]
    hit = _nearest_within(screen_pos, delivery_candidates, hit_radius)
    if hit is not None:
        return hit

    transit_candidates = [
        (node_id, mesh.network.nodes[node_id])
        for node_id in mesh.transit_ids
        if node_id in mesh.network.nodes
    ]
    return _nearest_within(screen_pos, transit_candidates, hit_radius)
