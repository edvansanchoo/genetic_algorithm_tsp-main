"""Decoder de capacidade: permutação de tokens → viagens com retorno ao depósito."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from traveling_salesman_problem.problem.delivery_mesh import (
    DeliveryMesh,
    delivery_segment_distance,
    delivery_segment_path,
)
from traveling_salesman_problem.problem.road_network import (
    EdgeKey,
    canonical_edge,
    path_distance,
    path_weighted_distance,
)
from traveling_salesman_problem.problem.vrp_models import (
    DEPOT_ID,
    Coordinate,
    DeliveryToken,
    Trip,
    TripStop,
)


@dataclass
class DecodedVehiclePlan:
    trips: List[Trip]
    total_distance: float
    priority_penalty: float
    fitness: float


def _token_multiset(tokens: List[DeliveryToken]) -> Counter:
    return Counter((token.point_id, token.quantity) for token in tokens)


def _invalid_plan() -> DecodedVehiclePlan:
    return DecodedVehiclePlan(
        trips=[],
        total_distance=float("inf"),
        priority_penalty=0.0,
        fitness=float("inf"),
    )


def _edges_from_path(path: List[str]) -> Set[EdgeKey]:
    edges: Set[EdgeKey] = set()
    for index in range(len(path) - 1):
        edges.add(canonical_edge(path[index], path[index + 1]))
    return edges


def _return_segment(
    mesh: DeliveryMesh,
    origin: Coordinate,
    destination: Coordinate,
    trip_edges: Set[EdgeKey],
    return_fallback_penalty: float,
) -> Optional[Tuple[float, List[str]]]:
    path = delivery_segment_path(
        mesh,
        origin,
        destination,
        forbidden_edges=trip_edges,
    )
    if path:
        cost = path_distance(mesh.network, path)
        return cost, path

    path = delivery_segment_path(
        mesh,
        origin,
        destination,
        used_edges=trip_edges,
        reuse_penalty=return_fallback_penalty,
    )
    if not path:
        return None
    cost = path_weighted_distance(
        mesh.network,
        path,
        trip_edges,
        return_fallback_penalty,
    )
    return cost, path


def decode_vehicle_permutation(
    tokens: List[DeliveryToken],
    permutation: List[DeliveryToken],
    depot: Coordinate,
    mesh: DeliveryMesh,
    capacity: int,
    priority_weight: float = 0.0,
    reuse_penalty: float = 1.75,
    return_fallback_penalty: float = 20.0,
) -> DecodedVehiclePlan:
    if capacity < 1:
        return _invalid_plan()
    if _token_multiset(tokens) != _token_multiset(permutation):
        return _invalid_plan()
    if not permutation:
        return DecodedVehiclePlan(
            trips=[],
            total_distance=0.0,
            priority_penalty=0.0,
            fitness=0.0,
        )

    trips: List[Trip] = []
    current_stops: List[TripStop] = [
        TripStop(node_id=DEPOT_ID, quantity=0, coordinate=depot)
    ]
    current_paths: List[List[str]] = []
    current_distance = 0.0
    current_load = 0
    last_coordinate = depot
    visit_order = 0
    priority_penalty = 0.0
    used_edges: Set[EdgeKey] = set()
    trip_edges: Set[EdgeKey] = set()

    def _record_path(path: List[str]) -> None:
        path_edges = _edges_from_path(path)
        used_edges.update(path_edges)
        trip_edges.update(path_edges)

    def traverse_non_return(
        from_coord: Coordinate,
        to_coord: Coordinate,
    ) -> Optional[Tuple[float, List[str]]]:
        path = delivery_segment_path(
            mesh,
            from_coord,
            to_coord,
            used_edges=used_edges,
            reuse_penalty=reuse_penalty,
        )
        if not path:
            return None
        cost = delivery_segment_distance(
            mesh,
            from_coord,
            to_coord,
            used_edges=used_edges,
            reuse_penalty=reuse_penalty,
        )
        if cost == float("inf"):
            return None
        _record_path(path)
        return cost, path

    def close_trip_returning_to_depot() -> Optional[DecodedVehiclePlan]:
        nonlocal current_stops, current_paths, current_distance, last_coordinate, trip_edges
        result = _return_segment(
            mesh,
            last_coordinate,
            depot,
            trip_edges,
            return_fallback_penalty,
        )
        if result is None:
            return _invalid_plan()
        cost, path = result
        current_distance += cost
        current_paths.append(path)
        used_edges.update(_edges_from_path(path))
        current_stops.append(
            TripStop(node_id=DEPOT_ID, quantity=0, coordinate=depot)
        )
        trips.append(
            Trip(
                stops=list(current_stops),
                distance=current_distance,
                path_node_ids=list(current_paths),
            )
        )
        current_stops = [
            TripStop(node_id=DEPOT_ID, quantity=0, coordinate=depot)
        ]
        current_paths = []
        current_distance = 0.0
        last_coordinate = depot
        trip_edges = set()
        return None

    for token in permutation:
        if current_load + token.quantity > capacity:
            if len(current_stops) > 1:
                failure = close_trip_returning_to_depot()
                if failure is not None:
                    return failure
                current_load = 0

        delivery_coordinate = mesh.network.nodes.get(token.point_id)
        if delivery_coordinate is None:
            delivery_coordinate = None
            for coordinate, node_id in mesh.coordinate_to_id.items():
                if node_id == token.point_id:
                    delivery_coordinate = coordinate
                    break
        if delivery_coordinate is None:
            return _invalid_plan()

        result = traverse_non_return(last_coordinate, delivery_coordinate)
        if result is None:
            return _invalid_plan()
        cost, path = result
        current_distance += cost
        current_paths.append(path)
        current_stops.append(
            TripStop(
                node_id=token.point_id,
                quantity=token.quantity,
                coordinate=delivery_coordinate,
            )
        )
        current_load += token.quantity
        last_coordinate = delivery_coordinate
        visit_order += 1
        priority_penalty += token.priority * visit_order

    failure = close_trip_returning_to_depot()
    if failure is not None:
        return failure

    total_distance = sum(trip.distance for trip in trips)
    fitness = total_distance + priority_weight * priority_penalty
    return DecodedVehiclePlan(
        trips=trips,
        total_distance=total_distance,
        priority_penalty=priority_penalty,
        fitness=fitness,
    )
