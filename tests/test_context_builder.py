"""Testes do construtor de contexto LLM."""

from traveling_salesman_problem.llm.context_builder import build_route_context, context_to_json
from traveling_salesman_problem.llm.session_history import SessionHistory
from traveling_salesman_problem.simulation.simulation_state import SimulationState


def test_build_route_context_contains_required_fields():
    simulation = SimulationState()
    simulation.initialize_headless()
    result = simulation.run_one_generation()
    plans = result[4]

    context = build_route_context(
        simulation=simulation,
        generation_number=result[0],
        total_fitness=result[1],
        total_distance=result[2],
        total_priority=result[3],
        plans=plans,
        session_history=SessionHistory(),
    )

    assert context["cenario"] == "hospitalar"
    assert "metricas" in context
    assert "entregas" in context
    assert "veiculos" in context
    assert len(context["entregas"]) > 0


def test_context_to_json_is_valid():
    context = {"geracao": 1, "metricas": {"fitness": 100.0}}
    json_text = context_to_json(context)
    assert '"geracao": 1' in json_text
    assert '"fitness": 100.0' in json_text


def test_build_route_context_filters_vehicle():
    simulation = SimulationState()
    simulation.initialize_headless()
    result = simulation.run_one_generation()
    plans = result[4]
    vehicle_ids = list(plans.keys())
    if not vehicle_ids:
        return

    context = build_route_context(
        simulation=simulation,
        generation_number=result[0],
        total_fitness=result[1],
        total_distance=result[2],
        total_priority=result[3],
        plans=plans,
        session_history=SessionHistory(),
        vehicle_id=vehicle_ids[0],
    )
    assert len(context["veiculos"]) == 1
    assert context["veiculos"][0]["id"] == vehicle_ids[0]
