"""Algoritmo guloso global com capacidade por viagem e pathfinding em grafo."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from delivery_simulation.models import (
    DEPOT_ID,
    MAX_CAPACITY,
    DeliveryPoint,
    RoadNetwork,
    SimulationConfig,
    SimulationResult,
    Stop,
    TransitNode,
    Trip,
    Vehicle,
)
from delivery_simulation.road_network import find_path, path_distance


@dataclass
class _ActiveTrip:
    stops: List[Stop] = field(default_factory=list)
    distance: float = 0.0
    visited_nodes: Set[str] = field(default_factory=set)


@dataclass(order=True)
class _Candidate:
    distance: float
    vehicle_id: int
    point_id: str
    delivery_amount: int = field(compare=False)


def _clone_points(delivery_points: List[DeliveryPoint]) -> List[DeliveryPoint]:
    return [
        DeliveryPoint(
            id=point.id,
            coordinate=point.coordinate,
            total_items=point.total_items,
            remaining_items=point.total_items,
        )
        for point in delivery_points
    ]


def _pending_points(points: List[DeliveryPoint]) -> List[DeliveryPoint]:
    return [point for point in points if point.remaining_items > 0]


def _is_transit_node(node_id: str) -> bool:
    return node_id.startswith("T")


def _blocked_for_pathfinding(blocked: Set[str], destination: str) -> Set[str]:
    """Trânsito e entregas visitadas podem ser reutilizados no caminho de volta."""
    if destination != DEPOT_ID:
        return set(blocked)
    return set()


def _existing_stop_ids(active_trip: _ActiveTrip) -> Set[str]:
    return {stop.point_id for stop in active_trip.stops}


def _finalize_trip(vehicle: Vehicle, active_trip: Optional[_ActiveTrip], network: RoadNetwork) -> None:
    if active_trip is None or not active_trip.stops:
        return
    vehicle.trips.append(Trip(stops=list(active_trip.stops), distance=active_trip.distance))
    vehicle.current_node_id = DEPOT_ID
    vehicle.current_position = network.nodes[DEPOT_ID]


def _traverse_path(
    vehicle: Vehicle,
    active_trip: _ActiveTrip,
    network: RoadNetwork,
    path: List[str],
    delivery_node: Optional[str],
    delivery_amount: int,
    record_transit_stops: bool = True,
) -> None:
    for index in range(1, len(path)):
        previous_id = path[index - 1]
        node_id = path[index]
        active_trip.distance += path_distance(network, [previous_id, node_id])

        is_delivery_stop = node_id == delivery_node and delivery_amount > 0
        if node_id == DEPOT_ID:
            active_trip.stops.append(Stop(DEPOT_ID, 0, is_transit=False))
        elif is_delivery_stop:
            active_trip.stops.append(Stop(node_id, delivery_amount, is_transit=False))
        elif _is_transit_node(node_id) and record_transit_stops:
            if node_id not in _existing_stop_ids(active_trip):
                active_trip.stops.append(Stop(node_id, 0, is_transit=True))

        if node_id != DEPOT_ID or index == len(path) - 1:
            active_trip.visited_nodes.add(node_id)

        vehicle.current_node_id = node_id
        vehicle.current_position = network.nodes[node_id]

    if path[0] == DEPOT_ID and len(path) > 1:
        active_trip.visited_nodes.add(DEPOT_ID)


def run_greedy_simulation(
    config: SimulationConfig,
    depot_coordinate,
    delivery_points: List[DeliveryPoint],
    road_network: RoadNetwork,
    transit_nodes: List[TransitNode],
) -> SimulationResult:
    points = _clone_points(delivery_points)
    vehicles = [
        Vehicle(
            id=index + 1,
            current_node_id=DEPOT_ID,
            current_position=road_network.nodes[DEPOT_ID],
            current_load=0,
        )
        for index in range(config.vehicle_count)
    ]
    active_trips: Dict[int, Optional[_ActiveTrip]] = {vehicle.id: None for vehicle in vehicles}

    while _pending_points(points):
        candidates: List[_Candidate] = []

        for vehicle in vehicles:
            remaining_capacity = MAX_CAPACITY - vehicle.current_load
            pending = _pending_points(points)
            blocked = active_trips[vehicle.id].visited_nodes if active_trips[vehicle.id] else set()
            vehicle_candidates: List[_Candidate] = []

            can_deliver = any(
                min(remaining_capacity, point.remaining_items) > 0 for point in pending
            )

            if remaining_capacity > 0 and can_deliver:
                for point in pending:
                    delivery_amount = min(remaining_capacity, point.remaining_items)
                    if delivery_amount <= 0:
                        continue
                    path = find_path(
                        road_network,
                        vehicle.current_node_id,
                        point.id,
                        _blocked_for_pathfinding(blocked, point.id),
                    )
                    if not path:
                        continue
                    vehicle_candidates.append(
                        _Candidate(
                            path_distance(road_network, path),
                            vehicle.id,
                            point.id,
                            delivery_amount,
                        )
                    )

            needs_depot_return = (
                vehicle.current_node_id != DEPOT_ID
                or vehicle.current_load > 0
                or active_trips[vehicle.id] is not None
            )
            if not vehicle_candidates and needs_depot_return:
                path = find_path(
                    road_network,
                    vehicle.current_node_id,
                    DEPOT_ID,
                    _blocked_for_pathfinding(blocked, DEPOT_ID),
                )
                if path:
                    vehicle_candidates.append(
                        _Candidate(
                            path_distance(road_network, path),
                            vehicle.id,
                            DEPOT_ID,
                            0,
                        )
                    )
            elif remaining_capacity == 0 or not can_deliver:
                if needs_depot_return:
                    path = find_path(
                        road_network,
                        vehicle.current_node_id,
                        DEPOT_ID,
                        _blocked_for_pathfinding(blocked, DEPOT_ID),
                    )
                    if path:
                        vehicle_candidates.append(
                            _Candidate(
                                path_distance(road_network, path),
                                vehicle.id,
                                DEPOT_ID,
                                0,
                            )
                        )

            candidates.extend(vehicle_candidates)

        if not candidates:
            for vehicle in vehicles:
                active_trip = active_trips[vehicle.id]
                if active_trip is None:
                    continue
                blocked = active_trip.visited_nodes
                path = find_path(
                    road_network,
                    vehicle.current_node_id,
                    DEPOT_ID,
                    set(),
                )
                if path:
                    candidates.append(
                        _Candidate(
                            path_distance(road_network, path),
                            vehicle.id,
                            DEPOT_ID,
                            0,
                        )
                    )

        if not candidates:
            raise RuntimeError(
                "Nenhum candidato disponível com entregas pendentes. "
                "Tente sortear posições novamente ou aumentar o raio de conexão."
            )

        chosen = min(candidates)
        vehicle = vehicles[chosen.vehicle_id - 1]
        blocked = active_trips[vehicle.id].visited_nodes if active_trips[vehicle.id] else set()

        if chosen.point_id == DEPOT_ID:
            active_trip = active_trips[vehicle.id]
            if active_trip is not None:
                path = find_path(
                    road_network,
                    vehicle.current_node_id,
                    DEPOT_ID,
                    _blocked_for_pathfinding(blocked, DEPOT_ID),
                )
                if path:
                    _traverse_path(
                        vehicle,
                        active_trip,
                        road_network,
                        path,
                        None,
                        0,
                        record_transit_stops=False,
                    )
                _finalize_trip(vehicle, active_trip, road_network)
            active_trips[vehicle.id] = None
            vehicle.current_load = 0
            continue

        point = next(item for item in points if item.id == chosen.point_id)
        active_trip = active_trips[vehicle.id]
        if active_trip is None:
            active_trip = _ActiveTrip(stops=[Stop(DEPOT_ID, 0)], distance=0.0)
            active_trips[vehicle.id] = active_trip

        path = find_path(
            road_network,
            vehicle.current_node_id,
            point.id,
            _blocked_for_pathfinding(blocked, point.id),
        )
        if not path:
            raise RuntimeError(f"Sem caminho para {point.id}")

        _traverse_path(
            vehicle,
            active_trip,
            road_network,
            path,
            delivery_node=point.id,
            delivery_amount=chosen.delivery_amount,
        )

        vehicle.current_load += chosen.delivery_amount
        point.remaining_items -= chosen.delivery_amount

        if point.id not in vehicle.assigned_points:
            vehicle.assigned_points.append(point.id)

    for vehicle in vehicles:
        active_trip = active_trips[vehicle.id]
        if active_trip is not None:
            blocked = active_trip.visited_nodes
            path = find_path(
                road_network,
                vehicle.current_node_id,
                DEPOT_ID,
                _blocked_for_pathfinding(blocked, DEPOT_ID),
            )
            if path:
                _traverse_path(
                    vehicle,
                    active_trip,
                    road_network,
                    path,
                    None,
                    0,
                    record_transit_stops=False,
                )
            _finalize_trip(vehicle, active_trip, road_network)
            active_trips[vehicle.id] = None
        vehicle.current_load = 0

    total_system_distance = sum(
        trip.distance for vehicle in vehicles for trip in vehicle.trips
    )

    final_points = [
        DeliveryPoint(
            id=point.id,
            coordinate=point.coordinate,
            total_items=point.total_items,
            remaining_items=0,
        )
        for point in points
    ]

    return SimulationResult(
        config=config,
        depot=depot_coordinate,
        delivery_points=final_points,
        vehicles=vehicles,
        total_system_distance=total_system_distance,
        road_network=road_network,
        transit_nodes=transit_nodes,
    )
