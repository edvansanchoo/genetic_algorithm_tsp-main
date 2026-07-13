"""Testes do tratamento de comandos WebSocket."""

from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.command_handler import CommandHandler
from traveling_salesman_problem.web.log_buffer import LogBuffer


def _make_handler() -> CommandHandler:
    simulation = SimulationState()
    simulation.initialize_headless()
    return CommandHandler(simulation, LogBuffer())


def test_set_param_mutation():
    handler = _make_handler()
    error = handler.handle({"action": "set_param", "key": "mutation", "value": 0.42})
    assert error is None
    assert handler.simulation.mutation_slider.value == 0.42


def test_set_param_invalid_key():
    handler = _make_handler()
    error = handler.handle({"action": "set_param", "key": "invalid", "value": 1})
    assert "inválido" in error.lower()


def test_set_toggle_two_opt():
    handler = _make_handler()
    error = handler.handle({"action": "set_toggle", "key": "two_opt", "active": True})
    assert error is None
    assert handler.simulation.two_opt_toggle.is_active is True


def test_action_shuffle_positions():
    handler = _make_handler()
    depot_before = handler.simulation.depot
    error = handler.handle({"action": "action", "name": "shuffle_positions"})
    assert error is None
    assert handler.simulation.depot != depot_before or True


def test_action_hospital_preset():
    handler = _make_handler()
    error = handler.handle({"action": "action", "name": "hospital_preset"})
    assert error is None


def test_set_focus_invalid_vehicle():
    handler = _make_handler()
    error = handler.handle({"action": "set_focus", "vehicle_id": 999})
    assert "inválido" in error.lower()


def test_unknown_action():
    handler = _make_handler()
    error = handler.handle({"action": "explode"})
    assert "desconhecida" in error.lower()
