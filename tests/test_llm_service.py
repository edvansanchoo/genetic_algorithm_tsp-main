"""Testes do serviço LLM."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from traveling_salesman_problem.llm.service import LlmService


class LlmServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_instructions(self):
        simulation_service = MagicMock()
        simulation_service.generation_number = 5
        simulation_service.total_fitness = 100.0
        simulation_service.total_distance = 50.0
        simulation_service.total_priority = 10.0
        simulation_service.plans = {}
        simulation_service.simulation = MagicMock()
        simulation_service.session_history = MagicMock()
        simulation_service.session_history.trend.return_value = {
            "melhoria_fitness": -5,
            "geracoes_desde_melhoria": 2,
        }
        simulation_service.session_history.daily_summary.return_value = {}
        simulation_service.session_history.weekly_summary.return_value = {}

        ollama = AsyncMock()
        ollama.chat.return_value = "# Instruções"

        service = LlmService(simulation_service, ollama)
        with patch(
            "traveling_salesman_problem.llm.service.build_route_context",
            return_value={"geracao": 5},
        ):
            result = await service.generate("instructions")
        self.assertEqual(result["type"], "instructions")
        self.assertIn("Instruções", result["content"])


if __name__ == "__main__":
    unittest.main()
