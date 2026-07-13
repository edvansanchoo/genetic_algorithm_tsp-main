"""Serialização do estado da simulação para JSON WebSocket."""

from __future__ import annotations

from typing import Dict, List, Optional

from traveling_salesman_problem.config.visual_theme import VisualTheme, priority_to_color
from traveling_salesman_problem.problem.vrp_decoder import (
    DecodedVehiclePlan,
    plan_blocked_crossing_penalty,
)
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.visualization.map_renderer import _trip_polyline_from_stored
from traveling_salesman_problem.visualization.route_panel import (
    build_route_panel_rows,
    filter_plans_by_focus,
)


VEHICLE_COLORS_UI = ["#2563eb", "#059669", "#dc2626", "#d97706", "#7c3aed"]
ELITE_PCT = 10


def _priority_served_pct(
    simulation: SimulationState,
    plans: Dict[int, DecodedVehiclePlan],
) -> int:
    critical_ids = {
        point.id for point in simulation.deliveries if point.priority >= 8
    }
    if not critical_ids:
        return 100

    visit_order: list[str] = []
    for vehicle_id in sorted(plans.keys()):
        plan = plans[vehicle_id]
        for trip in plan.trips:
            for stop in trip.stops:
                if stop.node_id != DEPOT_ID:
                    visit_order.append(stop.node_id)

    if not visit_order:
        return 0

    total = len(visit_order)
    served_early = 0
    for delivery_id in critical_ids:
        try:
            position = visit_order.index(delivery_id)
        except ValueError:
            continue
        if position / total <= 0.33:
            served_early += 1

    return round(served_early / len(critical_ids) * 100)


def _rgb_to_hex(color: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*color)


def _serialize_trip_polylines(mesh, trip) -> List[List[List[float]]]:
    points = _trip_polyline_from_stored(mesh, trip)
    if not points:
        return []
    return [[[float(x), float(y)] for x, y in points]]


def _serialize_plan(mesh, plan: DecodedVehiclePlan, capacity: int) -> dict:
    trips_payload = []
    total_load = 0
    for index, trip in enumerate(plan.trips, start=1):
        stops = [stop.node_id for stop in trip.stops]
        load = sum(
            stop.quantity for stop in trip.stops if stop.node_id != DEPOT_ID
        )
        total_load += load
        trips_payload.append(
            {
                "index": index,
                "stops": stops,
                "load": load,
                "polylines": _serialize_trip_polylines(mesh, trip),
            }
        )
    return {
        "distance": plan.total_distance,
        "load": total_load,
        "capacity": capacity,
        "priority_penalty": plan.priority_penalty,
        "fitness": plan.fitness,
        "trips": trips_payload,
    }


def _serialize_map(simulation: SimulationState) -> dict:
    bounds = simulation.map_bounds()
    depot = simulation.depot
    deliveries = []
    for point in simulation.deliveries:
        priority_color = priority_to_color(point.priority)
        deliveries.append(
            {
                "id": point.id,
                "x": float(point.coordinate[0]),
                "y": float(point.coordinate[1]),
                "priority": point.priority,
                "demand": point.demand,
                "color": _rgb_to_hex(priority_color),
            }
        )

    mesh_payload = {"edges": [], "transit_nodes": [], "blocked": []}
    if simulation.mesh is not None:
        mesh = simulation.mesh
        for node_a, node_b in mesh.network.edges:
            start = mesh.network.nodes[node_a]
            end = mesh.network.nodes[node_b]
            mesh_payload["edges"].append(
                [float(start[0]), float(start[1]), float(end[0]), float(end[1])]
            )
        for node_id in mesh.transit_ids:
            if node_id in mesh.network.nodes:
                coordinate = mesh.network.nodes[node_id]
                mesh_payload["transit_nodes"].append(
                    [float(coordinate[0]), float(coordinate[1])]
                )
        for coordinate in mesh.blocked_coordinates.values():
            mesh_payload["blocked"].append([float(coordinate[0]), float(coordinate[1])])

    return {
        "bounds": [float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3])],
        "depot": [float(depot[0]), float(depot[1])] if depot is not None else None,
        "deliveries": deliveries,
        "mesh": mesh_payload,
        "theme": {
            "vehicle_colors": [_rgb_to_hex(color) for color in VisualTheme.vehicle_route_colors],
            "depot_color": _rgb_to_hex(VisualTheme.depot_fill),
            "mesh_edge_color": _rgb_to_hex(VisualTheme.mesh_edge),
            "transit_color": _rgb_to_hex(VisualTheme.transit_fill),
            "blocked_color": _rgb_to_hex(VisualTheme.blocked_fill),
            "background_map": _rgb_to_hex(VisualTheme.background_map),
            "route_second_best": _rgb_to_hex(VisualTheme.route_second_best),
        },
    }


def _serialize_routes_panel(
    plans: Dict[int, DecodedVehiclePlan],
    capacity: int,
) -> list[dict]:
    rows = build_route_panel_rows(plans, capacity)
    payload = []
    for row in rows:
        entry = {"text": row.text}
        if row.is_vehicle_header:
            entry["type"] = "header"
            entry["vehicle_id"] = row.vehicle_id
        else:
            entry["type"] = "trip"
            entry["vehicle_id"] = row.vehicle_id
            entry["trip_index"] = row.trip_index
        payload.append(entry)
    return payload


def _count_trips(plans: Dict[int, DecodedVehiclePlan]) -> int:
    return sum(len(plan.trips) for plan in plans.values())


def serialize_state(
    simulation: SimulationState,
    *,
    generation_number: int,
    total_fitness: float,
    total_distance: float,
    total_priority: float,
    plans: Dict[int, DecodedVehiclePlan],
    runner_up_plans: Dict[int, DecodedVehiclePlan],
    histories: Dict[int, List[float]],
    running: bool,
    fps: float,
    animation: Optional[dict],
    logs: list[dict],
) -> dict:
    settings = simulation.settings
    capacity = simulation.capacity_slider.integer_value
    vehicle_count = simulation.vehicle_count_slider.integer_value
    visible_plans = filter_plans_by_focus(plans, simulation.focus_vehicle_id)

    plans_payload = {}
    if simulation.mesh is not None:
        for vehicle_id, plan in plans.items():
            plans_payload[str(vehicle_id)] = _serialize_plan(
                simulation.mesh,
                plan,
                capacity,
            )

    runner_up_payload = {}
    if simulation.mesh is not None:
        for vehicle_id, plan in runner_up_plans.items():
            runner_up_payload[str(vehicle_id)] = _serialize_plan(
                simulation.mesh,
                plan,
                capacity,
            )

    blocked_penalty = 0.0
    if simulation.mesh is not None:
        for plan in plans.values():
            blocked_penalty += plan_blocked_crossing_penalty(
                simulation.mesh,
                plan,
                settings.blocked_node_penalty,
            )

    total_demand = sum(point.demand for point in simulation.deliveries)
    delivered_load = sum(
        entry["load"]
        for entry in plans_payload.values()
    ) if plans_payload else 0

    return {
        "type": "state_update",
        "generation": generation_number,
        "running": running,
        "metrics": {
            "fitness": round(total_fitness, 2),
            "distance": round(total_distance, 2),
            "priority_penalty": round(total_priority, 2),
            "blocked_penalty": round(blocked_penalty, 2),
            "population_size": settings.population_size,
            "fps": round(fps, 1),
            "total_cost": round(total_fitness, 0),
            "priority_served_pct": _priority_served_pct(simulation, plans),
        },
        "params": {
            "mutation": simulation.mutation_slider.value,
            "priority_weight": simulation.priority_weight,
            "vehicle_count": vehicle_count,
            "capacity": capacity,
            "transit_count": simulation.transit_count_slider.integer_value,
            "param_ranges": {
                "mutation": [0.0, 1.0],
                "priority_weight": [0.0, 100.0],
                "vehicle_count": [1, settings.maximum_vehicle_count],
                "capacity": [
                    settings.minimum_capacity,
                    int(simulation.capacity_slider.maximum_value),
                ],
                "transit_count": [1, settings.maximum_mesh_nodes_per_type],
            },
        },
        "toggles": {
            "two_opt": simulation.two_opt_toggle.is_active,
            "show_mesh": simulation.show_mesh,
        },
        "focus": {
            "vehicle_id": simulation.focus_vehicle_id,
            "trip_index": simulation.focus_trip_index,
        },
        "summary": {
            "vehicles_active": len(simulation.vehicle_states),
            "vehicles_total": vehicle_count,
            "capacity_total": capacity,
            "deliveries_done": min(delivered_load, total_demand),
            "deliveries_total": total_demand,
            "trips_total": _count_trips(plans),
            "blocked_nodes": len(simulation.mesh.blocked_ids) if simulation.mesh else 0,
        },
        "map": _serialize_map(simulation),
        "plans": plans_payload,
        "runner_up": runner_up_payload,
        "histories": {str(key): list(values) for key, values in histories.items()},
        "animation": animation,
        "routes_panel": _serialize_routes_panel(visible_plans, capacity),
        "logs": logs,
        "display": {
            "vehicle_colors_ui": list(VEHICLE_COLORS_UI),
            "elite_pct": ELITE_PCT,
        },
    }
