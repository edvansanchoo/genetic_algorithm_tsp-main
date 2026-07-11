"""Testes da serialização WebSocket."""

import unittest

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.state_serializer import serialize_state


class StateSerializerTests(unittest.TestCase):
    def test_serialize_state_has_required_keys(self):
        simulation = SimulationState(settings=ApplicationSettings())
        simulation.initialize_headless()
        result = simulation.run_one_generation()
        generation_number, fitness, distance, priority, plans, runner_up, histories = result
        payload = serialize_state(
            simulation,
            generation_number=generation_number,
            total_fitness=fitness,
            total_distance=distance,
            total_priority=priority,
            plans=plans,
            runner_up_plans=runner_up,
            histories=histories,
            running=True,
            fps=30.0,
            animation=None,
            logs=[],
        )
        self.assertEqual(payload["type"], "state_update")
        for key in (
            "generation",
            "metrics",
            "params",
            "toggles",
            "map",
            "plans",
            "routes_panel",
            "display",
        ):
            self.assertIn(key, payload)

    def test_serialize_state_includes_derived_metrics(self):
        simulation = SimulationState(settings=ApplicationSettings())
        simulation.initialize_headless()
        result = simulation.run_one_generation()
        generation_number, fitness, distance, priority, plans, runner_up, histories = result
        payload = serialize_state(
            simulation,
            generation_number=generation_number,
            total_fitness=fitness,
            total_distance=distance,
            total_priority=priority,
            plans=plans,
            runner_up_plans=runner_up,
            histories=histories,
            running=True,
            fps=30.0,
            animation=None,
            logs=[],
        )
        self.assertIn("total_cost", payload["metrics"])
        self.assertIn("priority_served_pct", payload["metrics"])
        self.assertIsInstance(payload["metrics"]["total_cost"], (int, float))
        self.assertIsInstance(payload["metrics"]["priority_served_pct"], int)
        self.assertEqual(payload["display"]["vehicle_colors_ui"][0], "#2563eb")
        self.assertEqual(payload["display"]["elite_pct"], 10)


if __name__ == "__main__":
    unittest.main()
