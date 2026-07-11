"""Rotas desenháveis com um único veículo."""

import random
import unittest

from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.simulation.vehicle_genetic import plan_has_drawable_trips


class SingleVehicleRouteTests(unittest.TestCase):
    def test_rebuild_with_one_vehicle_has_drawable_best_plan(self) -> None:
        random.seed(42)
        simulation = SimulationState()
        simulation.initialize()
        simulation.vehicle_count_slider.value = 1.0
        simulation.rebuild_scenario()

        state = simulation.vehicle_states[0]
        self.assertGreater(len(state.tokens), 0)
        self.assertTrue(plan_has_drawable_trips(state.best_plan))
        self.assertLess(state.best_fitness, float("inf"))

        generation_number, _, distance, _, plans, _, _ = simulation.run_one_generation()
        self.assertEqual(generation_number, 1)
        self.assertGreater(distance, 0.0)
        self.assertIn(0, plans)


if __name__ == "__main__":
    unittest.main()
