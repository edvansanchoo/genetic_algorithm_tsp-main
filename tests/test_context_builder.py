"""Testes do construtor de contexto LLM."""

import unittest

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.llm.context_builder import build_route_context
from traveling_salesman_problem.llm.session_history import SessionHistory
from traveling_salesman_problem.simulation.simulation_state import SimulationState


class ContextBuilderTests(unittest.TestCase):
    def setUp(self):
        self.simulation = SimulationState(settings=ApplicationSettings())
        self.simulation.initialize_headless()
        for _ in range(3):
            self.simulation.run_one_generation()
        self.history = SessionHistory()

    def test_builds_required_keys(self):
        result = self.simulation.run_one_generation()
        gen, fitness, distance, priority, plans, *_ = result
        self.history.record_if_improved(
            gen,
            fitness,
            distance,
            80,
            len(self.simulation.mesh.blocked_ids) if self.simulation.mesh else 0,
            self.simulation.vehicle_count_slider.integer_value,
        )
        ctx = build_route_context(
            simulation=self.simulation,
            generation_number=gen,
            total_fitness=fitness,
            total_distance=distance,
            total_priority=priority,
            plans=plans,
            session_history=self.history,
        )
        self.assertEqual(ctx["cenario"], "hospitalar")
        self.assertIn("metricas", ctx)
        self.assertIn("entregas", ctx)
        self.assertIn("veiculos", ctx)
        self.assertIn("tendencia", ctx)
        self.assertTrue(len(ctx["entregas"]) > 0)
        self.assertTrue(len(ctx["veiculos"]) > 0)

    def test_filters_vehicle_when_requested(self):
        result = self.simulation.run_one_generation()
        _, fitness, distance, priority, plans, *_ = result
        vehicle_id = next(iter(plans.keys()))
        ctx = build_route_context(
            simulation=self.simulation,
            generation_number=1,
            total_fitness=fitness,
            total_distance=distance,
            total_priority=priority,
            plans=plans,
            session_history=SessionHistory(),
            vehicle_id=vehicle_id,
        )
        self.assertEqual(len(ctx["veiculos"]), 1)
        self.assertEqual(ctx["veiculos"][0]["id"], vehicle_id)


if __name__ == "__main__":
    unittest.main()
