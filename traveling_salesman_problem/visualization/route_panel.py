"""Formatação do painel de rotas VRP (D → … → D)."""

from __future__ import annotations

from typing import Dict, List, Optional

from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, Trip


def _stop_label(node_id: str) -> str:
    return "D" if node_id == DEPOT_ID else node_id


def format_trip_line(trip: Trip, trip_index: int, capacity: int) -> str:
    labels = [_stop_label(stop.node_id) for stop in trip.stops]
    path = " → ".join(labels)
    load = sum(stop.quantity for stop in trip.stops if stop.node_id != DEPOT_ID)
    return f"Viagem {trip_index}: {path}  ({load}/{capacity})"


def format_vehicle_section(
    vehicle_id: int,
    plan: DecodedVehiclePlan,
    capacity: int,
) -> List[str]:
    lines = [f"Veículo {vehicle_id + 1}"]
    for index, trip in enumerate(plan.trips, start=1):
        lines.append(f"  {format_trip_line(trip, index, capacity)}")
    return lines


def filter_plans_by_focus(
    plans: Dict[int, DecodedVehiclePlan],
    focus_vehicle_id: Optional[int],
) -> Dict[int, DecodedVehiclePlan]:
    if focus_vehicle_id is None:
        return dict(plans)
    if focus_vehicle_id not in plans:
        return {}
    return {focus_vehicle_id: plans[focus_vehicle_id]}
