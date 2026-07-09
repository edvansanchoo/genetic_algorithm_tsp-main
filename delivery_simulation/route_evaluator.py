"""Avalia permutação de entregas na rede de ruas com combustível."""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from delivery_simulation.fuel.models import (
    FUEL_STATION_ID_PREFIX,
    MAX_FUEL,
    RouteFuelReport,
)
from delivery_simulation.fuel.simulation import travel_with_fuel
from delivery_simulation.models import DEPOT_ID, MAX_CAPACITY, DeliveryTask, RoadNetwork, Stop, Trip
from delivery_simulation.road_network import path_distance

TaskPermutation = List[DeliveryTask]


@dataclass
class _ActiveTrip:
    stops: List[Stop] = field(default_factory=list)
    distance: float = 0.0
    visited_nodes: Set[str] = field(default_factory=set)


def _is_transit_node(node_id: str) -> bool:
    return node_id.startswith("T")


def _is_fuel_station(node_id: str) -> bool:
    return node_id.startswith(FUEL_STATION_ID_PREFIX)


def _station_ids(network: RoadNetwork) -> Set[str]:
    return {node_id for node_id in network.nodes if _is_fuel_station(node_id)}


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
        elif _is_fuel_station(node_id):
            if node_id not in _existing_stop_ids(active_trip):
                active_trip.stops.append(Stop(node_id, 0, is_fuel_station=True))
        elif _is_transit_node(node_id) and record_transit_stops:
            if node_id not in _existing_stop_ids(active_trip):
                active_trip.stops.append(Stop(node_id, 0, is_transit=True))

        if node_id != DEPOT_ID or index == len(path) - 1:
            active_trip.visited_nodes.add(node_id)

    if path and path[0] == DEPOT_ID and len(path) > 1:
        active_trip.visited_nodes.add(DEPOT_ID)


def _apply_fuel_travel(
    active_trip: _ActiveTrip,
    network: RoadNetwork,
    travel,
    delivery_node: Optional[str],
    delivery_amount: int,
    record_transit_stops: bool,
    report: RouteFuelReport,
) -> None:
    path_count = len(travel.paths)
    for path_index, path in enumerate(travel.paths):
        is_final = path_index == path_count - 1
        _append_path(
            active_trip,
            network,
            path,
            delivery_node if is_final else None,
            delivery_amount if is_final else 0,
            record_transit_stops,
        )
    report.legs.extend(travel.legs)
    report.stops.extend(travel.stops)
    report.total_distance += travel.distance
    for path in travel.paths:
        for node_id in path:
            if not report.expanded_node_ids or report.expanded_node_ids[-1] != node_id:
                report.expanded_node_ids.append(node_id)


def evaluate_permutation(
    tasks: List[DeliveryTask],
    permutation: TaskPermutation,
    road_network: RoadNetwork,
) -> tuple[float, List[Trip], RouteFuelReport]:
    empty_report = RouteFuelReport()
    if not tasks:
        return 0.0, [], empty_report

    if len(permutation) != len(tasks):
        return float("inf"), [], RouteFuelReport(is_feasible=False)

    station_ids = _station_ids(road_network)
    fuel = MAX_FUEL
    visited_stations: Set[str] = set()
    report = RouteFuelReport(final_fuel=fuel)
    leg_index = 0

    current_node = DEPOT_ID
    load = 0
    completed_trips: List[Trip] = []
    active_trip = _ActiveTrip(stops=[Stop(DEPOT_ID, 0)])
    report.expanded_node_ids = [DEPOT_ID]

    def _travel_to(destination: str, delivery_node: Optional[str], delivery_amount: int, record_transit: bool) -> bool:
        nonlocal fuel, visited_stations, current_node, leg_index
        blocked = _blocked_for_pathfinding(active_trip.visited_nodes, destination)
        travel = travel_with_fuel(
            road_network,
            current_node,
            destination,
            fuel,
            station_ids,
            visited_stations,
            blocked,
            leg_index_start=leg_index,
        )
        if not travel.is_feasible:
            report.is_feasible = False
            report.final_fuel = fuel
            return False
        _apply_fuel_travel(
            active_trip,
            road_network,
            travel,
            delivery_node,
            delivery_amount,
            record_transit,
            report,
        )
        fuel = travel.fuel_after
        visited_stations = set(travel.visited_stations)
        current_node = destination
        leg_index += len(travel.legs)
        report.final_fuel = fuel
        return True

    for task in permutation:
        if load + task.items > MAX_CAPACITY:
            if not _travel_to(DEPOT_ID, None, 0, False):
                return float("inf"), [], report
            completed_trips.append(Trip(stops=list(active_trip.stops), distance=active_trip.distance))
            active_trip = _ActiveTrip(stops=[Stop(DEPOT_ID, 0)])
            current_node = DEPOT_ID
            load = 0

        if not _travel_to(task.point_id, task.point_id, task.items, True):
            return float("inf"), [], report
        load += task.items

    if not _travel_to(DEPOT_ID, None, 0, False):
        return float("inf"), [], report
    completed_trips.append(Trip(stops=list(active_trip.stops), distance=active_trip.distance))

    total_distance = sum(trip.distance for trip in completed_trips)
    return total_distance, completed_trips, report
