"""Decoder de capacidade: permutação de tokens → viagens com retorno ao depósito."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List, Optional, Sequence, Set, Tuple

from traveling_salesman_problem.problem.delivery_mesh import (
    DeliveryMesh,
    delivery_segment_path,
)
from traveling_salesman_problem.problem.road_network import (
    EdgeKey,
    canonical_edge,
    path_distance,
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


def _nodes_from_path(path: List[str]) -> Set[str]:
    return set(path)


def _segment_with_plan_memory(
    mesh: DeliveryMesh,
    origin: Coordinate,
    destination: Coordinate,
    plan_edges: Set[EdgeKey],
    plan_nodes: Set[str],
) -> Optional[Tuple[float, List[str]]]:
    path = delivery_segment_path(
        mesh,
        origin,
        destination,
        forbidden_edges=plan_edges,
        forbidden_nodes=plan_nodes,
    )
    if not path:
        return None
    cost = path_distance(mesh.network, path)
    plan_edges.update(_edges_from_path(path))
    plan_nodes.update(_nodes_from_path(path))
    return cost, path


def path_blocked_crossing_penalty(
    mesh: DeliveryMesh,
    path: Sequence[str],
    penalty_per_node: float,
) -> float:
    return penalty_per_node * sum(
        1 for node_id in path if node_id in mesh.blocked_ids
    )


def plan_blocked_crossing_penalty(
    mesh: DeliveryMesh,
    plan: DecodedVehiclePlan,
    penalty_per_node: float,
) -> float:
    total = 0.0
    for trip in plan.trips:
        for path in trip.path_node_ids:
            total += path_blocked_crossing_penalty(mesh, path, penalty_per_node)
    return total


def plan_fitness_with_blocked_penalty(
    plan: DecodedVehiclePlan,
    mesh: DeliveryMesh,
    priority_weight: float,
    penalty_per_node: float,
) -> float:
    if plan.fitness == float("inf"):
        return float("inf")
    blocked_penalty = plan_blocked_crossing_penalty(mesh, plan, penalty_per_node)
    return (
        plan.total_distance
        + priority_weight * plan.priority_penalty
        + blocked_penalty
    )


def decode_vehicle_permutation(
    tokens: List[DeliveryToken],
    permutation: List[DeliveryToken],
    depot: Coordinate,
    mesh: DeliveryMesh,
    capacity: int,
    priority_weight: float = 0.0,
    blocked_node_penalty: float = 500.0,
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
    plan_edges: Set[EdgeKey] = set()
    plan_nodes: Set[str] = set()

    def close_trip_returning_to_depot() -> Optional[DecodedVehiclePlan]:
        nonlocal current_stops, current_paths, current_distance, last_coordinate
        result = _segment_with_plan_memory(
            mesh,
            last_coordinate,
            depot,
            plan_edges,
            plan_nodes,
        )
        if result is None:
            return _invalid_plan()
        cost, path = result
        current_distance += cost
        current_paths.append(path)
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

        result = _segment_with_plan_memory(
            mesh,
            last_coordinate,
            delivery_coordinate,
            plan_edges,
            plan_nodes,
        )
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
    plan = DecodedVehiclePlan(
        trips=trips,
        total_distance=total_distance,
        priority_penalty=priority_penalty,
        fitness=0.0,
    )
    plan.fitness = (
        total_distance
        + priority_weight * priority_penalty
        + plan_blocked_crossing_penalty(mesh, plan, blocked_node_penalty)
    )
    return plan
