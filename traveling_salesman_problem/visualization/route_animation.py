"""Helpers de animação ao longo das viagens VRP."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from traveling_salesman_problem.problem.delivery_mesh import (
    DeliveryMesh,
    delivery_segment_path,
    resolve_node_coordinate,
)
from traveling_salesman_problem.problem.road_network import Coordinate
from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import Trip

DEPOT_PAUSE_SECONDS = 0.8


def drawable_trip_indices(plan: DecodedVehiclePlan) -> List[int]:
    return [
        index
        for index, trip in enumerate(plan.trips)
        if len(trip.stops) >= 2
    ]


def _append_trip_polyline(
    mesh: DeliveryMesh,
    trip: Trip,
    points: List[Coordinate],
) -> None:
    if trip.path_node_ids:
        for path in trip.path_node_ids:
            path_coords = [
                resolve_node_coordinate(mesh, node_id) for node_id in path
            ]
            if points and path_coords:
                path_coords = path_coords[1:]
            points.extend(path_coords)
        return
    coordinates = [stop.coordinate for stop in trip.stops]
    for index in range(len(coordinates) - 1):
        path = delivery_segment_path(
            mesh,
            coordinates[index],
            coordinates[index + 1],
        )
        if not path:
            continue
        path_coords = [resolve_node_coordinate(mesh, node_id) for node_id in path]
        if points:
            path_coords = path_coords[1:]
        points.extend(path_coords)


def build_animation_polyline(
    mesh: DeliveryMesh,
    plan: DecodedVehiclePlan,
    trip_index: Optional[int] = None,
) -> List[Coordinate]:
    points: List[Coordinate] = []
    trips = plan.trips
    if trip_index is not None:
        if trip_index < 0 or trip_index >= len(trips):
            return []
        _append_trip_polyline(mesh, trips[trip_index], points)
        return points

    for trip in trips:
        _append_trip_polyline(mesh, trip, points)
    return points


def point_along_polyline(
    points: List[Coordinate],
    progress: float,
) -> Coordinate:
    if not points:
        return (0.0, 0.0)
    if len(points) == 1:
        return points[0]

    progress = progress % 1.0
    if progress < 0:
        progress += 1.0

    lengths = []
    total = 0.0
    for index in range(len(points) - 1):
        segment = math.hypot(
            points[index + 1][0] - points[index][0],
            points[index + 1][1] - points[index][1],
        )
        lengths.append(segment)
        total += segment

    if total <= 1e-9:
        return points[0]

    target = progress * total
    accumulated = 0.0
    for index, segment in enumerate(lengths):
        if accumulated + segment >= target:
            if segment <= 1e-9:
                return points[index]
            ratio = (target - accumulated) / segment
            x0, y0 = points[index]
            x1, y1 = points[index + 1]
            return (x0 + (x1 - x0) * ratio, y0 + (y1 - y0) * ratio)
        accumulated += segment
    return points[-1]


@dataclass
class TripAnimationState:
    current_trip_index: int = 0
    progress: float = 0.0
    depot_pause_remaining: float = 0.0

    def reset(self, trip_index: int = 0) -> None:
        self.current_trip_index = trip_index
        self.progress = 0.0
        self.depot_pause_remaining = 0.0


def advance_trip_animation(
    state: TripAnimationState,
    mesh: DeliveryMesh,
    plan: DecodedVehiclePlan,
    dt_seconds: float,
    *,
    locked_trip_index: Optional[int] = None,
    speed: float = 0.12,
    depot_pause_seconds: float = DEPOT_PAUSE_SECONDS,
) -> Tuple[Optional[Coordinate], Optional[int]]:
    """Avança animação e retorna (posição, índice da viagem ativa)."""
    drawable = drawable_trip_indices(plan)
    if not drawable:
        return None, None

    if locked_trip_index is not None:
        if locked_trip_index not in drawable:
            return None, locked_trip_index
        polyline = build_animation_polyline(mesh, plan, locked_trip_index)
        if len(polyline) < 2:
            return None, locked_trip_index
        state.current_trip_index = locked_trip_index
        state.depot_pause_remaining = 0.0
        state.progress = (state.progress + speed * dt_seconds) % 1.0
        return point_along_polyline(polyline, state.progress), locked_trip_index

    if state.current_trip_index not in drawable:
        state.current_trip_index = drawable[0]
        state.progress = 0.0
        state.depot_pause_remaining = 0.0

    if state.depot_pause_remaining > 0.0:
        state.depot_pause_remaining = max(0.0, state.depot_pause_remaining - dt_seconds)
        polyline = build_animation_polyline(mesh, plan, state.current_trip_index)
        if len(polyline) >= 1:
            return polyline[-1], state.current_trip_index
        return None, state.current_trip_index

    polyline = build_animation_polyline(mesh, plan, state.current_trip_index)
    if len(polyline) < 2:
        return None, state.current_trip_index

    state.progress += speed * dt_seconds
    if state.progress >= 1.0:
        state.progress = 0.0
        state.depot_pause_remaining = depot_pause_seconds
        current_position = drawable.index(state.current_trip_index)
        next_position = (current_position + 1) % len(drawable)
        state.current_trip_index = drawable[next_position]
        return polyline[-1], drawable[current_position]

    return point_along_polyline(polyline, state.progress), state.current_trip_index
