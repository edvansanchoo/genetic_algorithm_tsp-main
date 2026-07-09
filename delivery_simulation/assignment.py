"""Facade de simulação e extração de atribuições."""

from typing import List

from delivery_simulation.models import (
    Coordinate,
    DeliveryPoint,
    DeliveryTask,
    DEPOT_ID,
    RoadNetwork,
    SimulationConfig,
    SimulationResult,
    TransitNode,
)
from delivery_simulation.routing import run_greedy_simulation


def run_simulation(
    config: SimulationConfig,
    depot: Coordinate,
    delivery_points: List[DeliveryPoint],
    road_network: RoadNetwork,
    transit_nodes: List[TransitNode],
) -> SimulationResult:
    return run_greedy_simulation(
        config,
        depot,
        delivery_points,
        road_network,
        transit_nodes,
    )


def extract_vehicle_assignments(result: SimulationResult) -> dict[int, list[DeliveryTask]]:
    assignments: dict[int, list[DeliveryTask]] = {}

    for vehicle in result.vehicles:
        tasks: list[DeliveryTask] = []
        for trip in vehicle.trips:
            for stop in trip.stops:
                if stop.is_transit:
                    continue
                if stop.point_id == DEPOT_ID:
                    continue
                if stop.items_delivered <= 0:
                    continue
                tasks.append(DeliveryTask(stop.point_id, stop.items_delivered))
        assignments[vehicle.id] = tasks

    return assignments
