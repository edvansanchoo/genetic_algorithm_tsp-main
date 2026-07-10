"""Simulador guloso de distribuição de entregas."""

from delivery_simulation.assignment import extract_vehicle_assignments, run_simulation
from delivery_simulation.fuel.models import INITIAL_FUEL, MAX_FUEL, GasStation, RouteFuelReport
from delivery_simulation.fuel.placement import place_gas_stations
from delivery_simulation.fuel.simulation import travel_with_fuel
from delivery_simulation.models import (
    DeliveryPoint,
    DeliveryTask,
    RoadNetwork,
    SimulationConfig,
    SimulationResult,
    TransitNode,
    VALID_TOTAL_ITEMS,
)
from delivery_simulation.order_generator import distribute_items
from delivery_simulation.point_generator import generate_depot_and_points
from delivery_simulation.reporter import count_total_trips, format_simulation_result
from delivery_simulation.road_network import (
    build_connected_network,
    build_road_network,
    find_path,
    generate_transit_nodes,
    path_distance,
)
from delivery_simulation.route_evaluator import evaluate_permutation
from delivery_simulation.vehicle_genetic import (
    VehicleGeneticState,
    initialize_vehicle_genetic,
    run_vehicle_generation,
)

__all__ = [
    "DeliveryPoint",
    "DeliveryTask",
    "GasStation",
    "INITIAL_FUEL",
    "MAX_FUEL",
    "RoadNetwork",
    "RouteFuelReport",
    "SimulationConfig",
    "SimulationResult",
    "TransitNode",
    "VALID_TOTAL_ITEMS",
    "VehicleGeneticState",
    "build_connected_network",
    "build_road_network",
    "count_total_trips",
    "distribute_items",
    "evaluate_permutation",
    "extract_vehicle_assignments",
    "find_path",
    "format_simulation_result",
    "generate_depot_and_points",
    "generate_transit_nodes",
    "initialize_vehicle_genetic",
    "path_distance",
    "place_gas_stations",
    "run_simulation",
    "run_vehicle_generation",
    "travel_with_fuel",
]
