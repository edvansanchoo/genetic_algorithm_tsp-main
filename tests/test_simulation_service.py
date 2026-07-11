"""Testes do serviço de simulação Web."""

import asyncio
import unittest

from traveling_salesman_problem.web.simulation_service import SimulationService


class SimulationServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_simulation_service_emits_state_update(self):
        service = SimulationService()
        service.startup()
        service.paused = True
        payloads = []

        async def capture(payload):
            payloads.append(payload)

        await service.run_loop(capture, max_ticks=1)
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["type"], "state_update")


if __name__ == "__main__":
    unittest.main()
