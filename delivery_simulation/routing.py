"""Algoritmo guloso global com capacidade por viagem."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from delivery_simulation.distance import euclidean
from delivery_simulation.models import (
    DEPOT_ID,
    MAX_CAPACITY,
    Coordinate,
    DeliveryPoint,
    SimulationConfig,
    SimulationResult,
    Stop,
    Trip,
    Vehicle,
)


@dataclass
class _ActiveTrip:
    stops: List[Stop] = field(default_factory=list)
    distance: float = 0.0


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


def _append_depot_return(active_trip: _ActiveTrip, vehicle: Vehicle, depot: Coordinate) -> None:
    if vehicle.current_position == depot:
        active_trip.stops.append(Stop(DEPOT_ID, 0))
        return
    segment_distance = euclidean(vehicle.current_position, depot)
    active_trip.distance += segment_distance
    active_trip.stops.append(Stop(DEPOT_ID, 0))
    vehicle.current_position = depot


def _finalize_trip(vehicle: Vehicle, active_trip: Optional[_ActiveTrip]) -> None:
    if active_trip is None or not active_trip.stops:
        return
    vehicle.trips.append(Trip(stops=list(active_trip.stops), distance=active_trip.distance))


def run_greedy_simulation(
    config: SimulationConfig,
    depot: Coordinate,
    delivery_points: List[DeliveryPoint],
) -> SimulationResult:
    points = _clone_points(delivery_points)
    vehicles = [
        Vehicle(id=index + 1, current_position=depot, current_load=0)
        for index in range(config.vehicle_count)
    ]
    active_trips: Dict[int, Optional[_ActiveTrip]] = {vehicle.id: None for vehicle in vehicles}

    while _pending_points(points):
        candidates: List[_Candidate] = []

        for vehicle in vehicles:
            remaining_capacity = MAX_CAPACITY - vehicle.current_load
            pending = _pending_points(points)

            can_deliver = any(
                min(remaining_capacity, point.remaining_items) > 0 for point in pending
            )

            if remaining_capacity == 0 or not can_deliver:
                if vehicle.current_position != depot or vehicle.current_load > 0:
                    candidates.append(
                        _Candidate(
                            euclidean(vehicle.current_position, depot),
                            vehicle.id,
                            DEPOT_ID,
                            0,
                        )
                    )
                continue

            for point in pending:
                delivery_amount = min(remaining_capacity, point.remaining_items)
                if delivery_amount <= 0:
                    continue
                candidates.append(
                    _Candidate(
                        euclidean(vehicle.current_position, point.coordinate),
                        vehicle.id,
                        point.id,
                        delivery_amount,
                    )
                )

        if not candidates:
            raise RuntimeError("Nenhum candidato disponível com entregas pendentes")

        chosen = min(candidates)
        vehicle = vehicles[chosen.vehicle_id - 1]

        if chosen.point_id == DEPOT_ID:
            active_trip = active_trips[vehicle.id]
            if active_trip is not None:
                _append_depot_return(active_trip, vehicle, depot)
                _finalize_trip(vehicle, active_trip)
            active_trips[vehicle.id] = None
            vehicle.current_load = 0
            continue

        point = next(item for item in points if item.id == chosen.point_id)
        active_trip = active_trips[vehicle.id]
        if active_trip is None:
            active_trip = _ActiveTrip(stops=[Stop(DEPOT_ID, 0)], distance=0.0)
            active_trips[vehicle.id] = active_trip

        segment_distance = euclidean(vehicle.current_position, point.coordinate)
        active_trip.distance += segment_distance
        active_trip.stops.append(Stop(point.id, chosen.delivery_amount))

        vehicle.current_position = point.coordinate
        vehicle.current_load += chosen.delivery_amount
        point.remaining_items -= chosen.delivery_amount

        if point.id not in vehicle.assigned_points:
            vehicle.assigned_points.append(point.id)

    for vehicle in vehicles:
        active_trip = active_trips[vehicle.id]
        if active_trip is not None:
            _append_depot_return(active_trip, vehicle, depot)
            _finalize_trip(vehicle, active_trip)
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
        depot=depot,
        delivery_points=final_points,
        vehicles=vehicles,
        total_system_distance=total_system_distance,
    )
