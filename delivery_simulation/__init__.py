"""Simulador guloso de distribuição de entregas."""

from delivery_simulation.assignment import run_simulation
from delivery_simulation.models import (
    DeliveryPoint,
    SimulationConfig,
    SimulationResult,
    VALID_TOTAL_ITEMS,
)
from delivery_simulation.order_generator import distribute_items
from delivery_simulation.point_generator import generate_depot_and_points
from delivery_simulation.reporter import count_total_trips, format_simulation_result

__all__ = [
    "DeliveryPoint",
    "SimulationConfig",
    "SimulationResult",
    "VALID_TOTAL_ITEMS",
    "count_total_trips",
    "distribute_items",
    "format_simulation_result",
    "generate_depot_and_points",
    "run_simulation",
]
