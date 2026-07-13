"""Monta contexto compacto para prompts LLM."""

from __future__ import annotations

import json
from typing import Dict, Optional

from traveling_salesman_problem.llm.session_history import SessionHistory
from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.state_serializer import _priority_served_pct


def _serialize_vehicle(vehicle_id: int, plan: DecodedVehiclePlan, capacity: int) -> dict:
    trips = []
    total_load = 0
    for trip in plan.trips:
        stops = ["D" if stop.node_id == DEPOT_ID else stop.node_id for stop in trip.stops]
        load = sum(stop.quantity for stop in trip.stops if stop.node_id != DEPOT_ID)
        total_load += load
        trips.append({"paradas": stops, "carga": load})
    return {
        "id": vehicle_id,
        "distancia": round(plan.total_distance, 2),
        "carga": total_load,
        "capacidade": capacity,
        "viagens": trips,
    }


def build_route_context(
    *,
    simulation: SimulationState,
    generation_number: int,
    total_fitness: float,
    total_distance: float,
    total_priority: float,
    plans: Dict[int, DecodedVehiclePlan],
    session_history: SessionHistory,
    vehicle_id: Optional[int] = None,
) -> dict:
    capacity = simulation.capacity_slider.integer_value
    priority_pct = _priority_served_pct(simulation, plans)
    blocked = len(simulation.mesh.blocked_ids) if simulation.mesh else 0

    deliveries = [
        {
            "id": point.id,
            "prioridade": point.priority,
            "demanda": point.demand,
            "coords": [round(point.coordinate[0], 1), round(point.coordinate[1], 1)],
        }
        for point in simulation.deliveries
    ]

    vehicle_items = sorted(plans.items(), key=lambda item: item[0])
    if vehicle_id is not None:
        vehicle_items = [(vid, plan) for vid, plan in vehicle_items if vid == vehicle_id]

    depot = None
    if simulation.depot is not None:
        depot = [round(simulation.depot[0], 1), round(simulation.depot[1], 1)]

    return {
        "cenario": "hospitalar",
        "geracao": generation_number,
        "metricas": {
            "fitness": round(total_fitness, 2),
            "distancia": round(total_distance, 2),
            "penalidade_prioridade": round(total_priority, 2),
            "prioridade_pct": priority_pct,
        },
        "deposito": depot,
        "entregas": deliveries,
        "veiculos": [_serialize_vehicle(vid, plan, capacity) for vid, plan in vehicle_items],
        "bloqueios": blocked,
        "tendencia": session_history.trend(generation_number, total_fitness),
        "historico_sessao": session_history.daily_summary(),
        "historico_semanal": session_history.weekly_summary(),
    }


def context_to_json(context: dict) -> str:
    return json.dumps(context, ensure_ascii=False, indent=2)
