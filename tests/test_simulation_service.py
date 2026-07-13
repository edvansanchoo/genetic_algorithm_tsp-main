"""Testes do serviço de simulação Web."""

import asyncio

import pytest

from traveling_salesman_problem.web.simulation_service import SimulationService


def test_startup_initializes_simulation():
    service = SimulationService()
    service.startup()
    assert service.command_handler is not None
    assert service.simulation.mesh is not None


def test_pause_and_resume():
    service = SimulationService()
    service.startup()
    assert service.handle_command({"action": "pause"}) is None
    assert service.paused is True
    assert service.handle_command({"action": "resume"}) is None
    assert service.paused is False


def test_build_state_payload_type():
    service = SimulationService()
    service.startup()
    payload = service.build_state_payload()
    assert payload["type"] == "state_update"
    assert "generation" in payload


@pytest.mark.asyncio
async def test_run_loop_broadcasts_updates():
    service = SimulationService()
    service.startup()
    received: list[dict] = []

    async def capture(payload: dict) -> None:
        received.append(payload)

    await service.run_loop(capture, max_ticks=2)
    assert len(received) == 2
    assert all(item["type"] == "state_update" for item in received)
    assert received[-1]["generation"] >= received[0]["generation"]
