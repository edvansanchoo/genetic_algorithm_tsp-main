"""Avalia permutação de entregas na rede de ruas."""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from delivery_simulation.models import DEPOT_ID, MAX_CAPACITY, DeliveryTask, RoadNetwork, Stop, Trip
from delivery_simulation.road_network import find_path, path_distance

TaskPermutation = List[DeliveryTask]


@dataclass
class _ActiveTrip:
    stops: List[Stop] = field(default_factory=list)
    distance: float = 0.0
    visited_nodes: Set[str] = field(default_factory=set)


def _is_transit_node(node_id: str) -> bool:
    return node_id.startswith("T")


def _blocked_for_pathfinding(blocked: Set[str], destination: str) -> Set[str]:
    if destination != DEPOT_ID:
        return set(blocked)
    return {
        node_id
        for node_id in blocked
        if not _is_transit_node(node_id) and node_id != DEPOT_ID
    }


def _existing_stop_ids(active_trip: _ActiveTrip) -> Set[str]:
    return {stop.point_id for stop in active_trip.stops}


def _append_path(
    active_trip: _ActiveTrip,
    network: RoadNetwork,
    path: List[str],
    delivery_node: Optional[str],
    delivery_amount: int,
    record_transit_stops: bool,
) -> None:
    for index in range(1, len(path)):
        previous_id = path[index - 1]
        node_id = path[index]
        active_trip.distance += path_distance(network, [previous_id, node_id])

        is_delivery = node_id == delivery_node and delivery_amount > 0
        if node_id == DEPOT_ID:
            active_trip.stops.append(Stop(DEPOT_ID, 0, is_transit=False))
        elif is_delivery:
            active_trip.stops.append(Stop(node_id, delivery_amount, is_transit=False))
        elif _is_transit_node(node_id) and record_transit_stops:
            if node_id not in _existing_stop_ids(active_trip):
                active_trip.stops.append(Stop(node_id, 0, is_transit=True))

        if node_id != DEPOT_ID or index == len(path) - 1:
            active_trip.visited_nodes.add(node_id)

    if path and path[0] == DEPOT_ID and len(path) > 1:
        active_trip.visited_nodes.add(DEPOT_ID)


def evaluate_permutation(
    tasks: List[DeliveryTask],
    permutation: TaskPermutation,
    road_network: RoadNetwork,
) -> tuple[float, List[Trip]]:
    if not tasks:
        return 0.0, []

    if len(permutation) != len(tasks):
        return float("inf"), []

    current_node = DEPOT_ID
    load = 0
    completed_trips: List[Trip] = []
    active_trip = _ActiveTrip(stops=[Stop(DEPOT_ID, 0)])

    for task in permutation:
        if load + task.items > MAX_CAPACITY:
            blocked = active_trip.visited_nodes
            path = find_path(
                road_network,
                current_node,
                DEPOT_ID,
                _blocked_for_pathfinding(blocked, DEPOT_ID),
            )
            if not path:
                return float("inf"), []
            _append_path(active_trip, road_network, path, None, 0, record_transit_stops=False)
            completed_trips.append(Trip(stops=list(active_trip.stops), distance=active_trip.distance))
            active_trip = _ActiveTrip(stops=[Stop(DEPOT_ID, 0)])
            current_node = DEPOT_ID
            load = 0

        blocked = active_trip.visited_nodes
        path = find_path(
            road_network,
            current_node,
            task.point_id,
            _blocked_for_pathfinding(blocked, task.point_id),
        )
        if not path:
            return float("inf"), []
        _append_path(
            active_trip,
            road_network,
            path,
            task.point_id,
            task.items,
            record_transit_stops=True,
        )
        current_node = task.point_id
        load += task.items

    blocked = active_trip.visited_nodes
    path = find_path(
        road_network,
        current_node,
        DEPOT_ID,
        _blocked_for_pathfinding(blocked, DEPOT_ID),
    )
    if not path:
        return float("inf"), []
    _append_path(active_trip, road_network, path, None, 0, record_transit_stops=False)
    completed_trips.append(Trip(stops=list(active_trip.stops), distance=active_trip.distance))

    total_distance = sum(trip.distance for trip in completed_trips)
    return total_distance, completed_trips
