"""Helpers de animação ao longo das viagens VRP."""

from __future__ import annotations

import math
from typing import List

from traveling_salesman_problem.problem.delivery_mesh import (
    DeliveryMesh,
    delivery_segment_path,
    resolve_node_coordinate,
)
from traveling_salesman_problem.problem.road_network import Coordinate
from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan


def build_animation_polyline(
    mesh: DeliveryMesh,
    plan: DecodedVehiclePlan,
) -> List[Coordinate]:
    points: List[Coordinate] = []
    for trip in plan.trips:
        if trip.path_node_ids:
            for path in trip.path_node_ids:
                path_coords = [
                    resolve_node_coordinate(mesh, node_id) for node_id in path
                ]
                if points and path_coords:
                    path_coords = path_coords[1:]
                points.extend(path_coords)
            continue
        coordinates = [stop.coordinate for stop in trip.stops]
        for index in range(len(coordinates) - 1):
            path = delivery_segment_path(
                mesh,
                coordinates[index],
                coordinates[index + 1],
            )
            if not path:
                continue
            path_coords = [
                resolve_node_coordinate(mesh, node_id) for node_id in path
            ]
            if points:
                path_coords = path_coords[1:]
            points.extend(path_coords)
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
