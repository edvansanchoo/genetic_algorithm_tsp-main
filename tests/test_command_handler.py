"""Testes do tratamento de comandos Web."""

import unittest

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.command_handler import CommandHandler
from traveling_salesman_problem.web.log_buffer import LogBuffer


class CommandHandlerTests(unittest.TestCase):
    def setUp(self):
        self.simulation = SimulationState(settings=ApplicationSettings())
        self.simulation.initialize_headless()
        self.handler = CommandHandler(self.simulation, LogBuffer())

    def test_set_param_mutation(self):
        error = self.handler.handle(
            {
                "type": "command",
                "action": "set_param",
                "key": "mutation",
                "value": 0.25,
            }
        )
        self.assertIsNone(error)
        self.assertEqual(self.simulation.mutation_slider.value, 0.25)

    def test_action_shuffle_positions(self):
        old_depot = self.simulation.depot
        error = self.handler.handle(
            {
                "type": "command",
                "action": "action",
                "name": "shuffle_positions",
            }
        )
        self.assertIsNone(error)
        self.assertNotEqual(self.simulation.depot, old_depot)

    def test_set_focus_vehicle(self):
        error = self.handler.handle(
            {
                "type": "command",
                "action": "set_focus",
                "vehicle_id": 0,
                "trip_index": None,
            }
        )
        self.assertIsNone(error)
        self.assertEqual(self.simulation.focus_vehicle_id, 0)

    def test_toggle_blocked_at_map_coordinate(self):
        depot = self.simulation.depot
        self.assertIsNotNone(depot)
        error = self.handler.handle(
            {
                "type": "command",
                "action": "toggle_blocked",
                "map_x": depot[0],
                "map_y": depot[1],
            }
        )
        self.assertIsNone(error)
        self.assertIn(DEPOT_ID, self.simulation.mesh.blocked_ids)


if __name__ == "__main__":
    unittest.main()
