"""Testes de paridade do bloqueio manual via Web."""

import unittest

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID
from traveling_salesman_problem.simulation.simulation_state import SimulationState


class WebBlockedToggleTests(unittest.TestCase):
    def test_web_toggle_blocked_matches_simulation_state(self):
        simulation = SimulationState(settings=ApplicationSettings())
        simulation.initialize_headless()
        depot = simulation.depot
        self.assertIsNotNone(depot)
        changed = simulation.toggle_blocked_at((int(depot[0]), int(depot[1])))
        self.assertTrue(changed)
        self.assertIn(DEPOT_ID, simulation.mesh.blocked_ids)


if __name__ == "__main__":
    unittest.main()
