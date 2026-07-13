"""Testes da serialização de estado para WebSocket."""

from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.state_serializer import serialize_state


def test_serialize_state_structure():
    simulation = SimulationState()
    simulation.initialize_headless()
    result = simulation.run_one_generation()

    payload = serialize_state(
        simulation,
        generation_number=result[0],
        total_fitness=result[1],
        total_distance=result[2],
        total_priority=result[3],
        plans=result[4],
        runner_up_plans=result[5],
        histories=result[6],
        running=True,
        fps=30.0,
        animation=None,
        logs=[],
    )

    assert payload["type"] == "state_update"
    assert payload["generation"] == result[0]
    assert "metrics" in payload
    assert "map" in payload
    assert "params" in payload
    assert "plans" in payload
    assert payload["map"]["depot"] is not None
    assert len(payload["map"]["deliveries"]) > 0


def test_serialize_state_param_ranges():
    simulation = SimulationState()
    simulation.initialize_headless()
    payload = serialize_state(
        simulation,
        generation_number=0,
        total_fitness=0.0,
        total_distance=0.0,
        total_priority=0.0,
        plans={},
        runner_up_plans={},
        histories={},
        running=False,
        fps=0.0,
        animation=None,
        logs=[],
    )
    ranges = payload["params"]["param_ranges"]
    assert ranges["mutation"] == [0.0, 1.0]
    assert ranges["vehicle_count"][0] >= 1
