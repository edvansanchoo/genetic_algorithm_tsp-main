"""Facade de simulação."""

from typing import List

from delivery_simulation.models import Coordinate, DeliveryPoint, SimulationConfig, SimulationResult
from delivery_simulation.routing import run_greedy_simulation


def run_simulation(
    config: SimulationConfig,
    depot: Coordinate,
    delivery_points: List[DeliveryPoint],
) -> SimulationResult:
    return run_greedy_simulation(config, depot, delivery_points)
