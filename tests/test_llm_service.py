"""Testes do serviço LLM (mock Ollama)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from traveling_salesman_problem.llm.ollama_client import OllamaClient
from traveling_salesman_problem.llm.service import LlmService
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.simulation_service import SimulationService


@pytest.fixture
def llm_service():
    sim_service = SimulationService()
    sim_service.startup()
    sim_service.simulation.run_one_generation()

    ollama = MagicMock(spec=OllamaClient)
    ollama.chat = AsyncMock(return_value="Relatório gerado.")
    ollama.health_check = AsyncMock(return_value={"ok": True, "model": "test", "message": "ok"})
    return LlmService(sim_service, ollama), ollama


@pytest.mark.asyncio
async def test_generate_calls_ollama(llm_service):
    service, ollama = llm_service
    result = await service.generate("daily_report")
    assert result["type"] == "daily_report"
    assert result["content"] == "Relatório gerado."
    ollama.chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_returns_updated_history(llm_service):
    service, ollama = llm_service
    result = await service.chat("Qual a distância total?")
    assert result["reply"] == "Relatório gerado."
    assert len(result["history"]) == 2
    assert result["history"][0]["role"] == "user"
    ollama.chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_delegates_to_client(llm_service):
    service, ollama = llm_service
    health = await service.health()
    assert health["ok"] is True
    ollama.health_check.assert_awaited_once()
