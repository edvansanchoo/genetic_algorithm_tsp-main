"""Formatação do painel de rotas VRP (D → … → D)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, Trip

ROUTE_PANEL_ROW_HEIGHT = 16


def _stop_label(node_id: str) -> str:
    return "DEPOT" if node_id == DEPOT_ID else node_id


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


@dataclass(frozen=True)
class RoutePanelRow:
    text: str
    is_vehicle_header: bool
    vehicle_id: Optional[int] = None
    trip_index: Optional[int] = None


def build_route_panel_rows(
    plans: Dict[int, DecodedVehiclePlan],
    capacity: int,
) -> List[RoutePanelRow]:
    rows: List[RoutePanelRow] = []
    for vehicle_id, plan in sorted(plans.items()):
        rows.append(
            RoutePanelRow(
                text=f"Veículo {vehicle_id + 1}",
                is_vehicle_header=True,
                vehicle_id=vehicle_id,
            )
        )
        for index, trip in enumerate(plan.trips, start=1):
            rows.append(
                RoutePanelRow(
                    text=f"  {format_trip_line(trip, index, capacity)}",
                    is_vehicle_header=False,
                    vehicle_id=vehicle_id,
                    trip_index=index - 1,
                )
            )
    return rows


def hit_test_route_panel(
    rows: List[RoutePanelRow],
    mouse_x: int,
    mouse_y: int,
    panel_x: int,
    panel_y: int,
    panel_width: int,
) -> Optional[Tuple[str, int, Optional[int]]]:
    """Retorna ('header'|'trip', vehicle_id, trip_index) ou None."""
    if mouse_x < panel_x or mouse_x >= panel_x + panel_width:
        return None
    row_index = (mouse_y - panel_y) // ROUTE_PANEL_ROW_HEIGHT
    if row_index < 0 or row_index >= len(rows):
        return None
    row = rows[row_index]
    if row.vehicle_id is None:
        return None
    if row.is_vehicle_header:
        return ("header", row.vehicle_id, None)
    if row.trip_index is None:
        return None
    return ("trip", row.vehicle_id, row.trip_index)
