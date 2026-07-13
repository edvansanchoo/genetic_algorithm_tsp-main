"""Testes do histórico de sessão LLM."""

import unittest

from traveling_salesman_problem.llm.session_history import SessionHistory


class SessionHistoryTests(unittest.TestCase):
    def test_records_only_on_fitness_improvement(self):
        history = SessionHistory(max_entries=10)
        self.assertTrue(
            history.record_if_improved(
                generation=1,
                fitness=100.0,
                distance=50.0,
                priority_served_pct=80,
                blocked_nodes=0,
                vehicle_count=2,
            )
        )
        self.assertEqual(len(history.all_snapshots()), 1)

        self.assertFalse(
            history.record_if_improved(
                generation=2,
                fitness=100.0,
                distance=49.0,
                priority_served_pct=80,
                blocked_nodes=0,
                vehicle_count=2,
            )
        )
        self.assertEqual(len(history.all_snapshots()), 1)

        self.assertTrue(
            history.record_if_improved(
                generation=3,
                fitness=90.0,
                distance=48.0,
                priority_served_pct=85,
                blocked_nodes=1,
                vehicle_count=2,
            )
        )
        self.assertEqual(len(history.all_snapshots()), 2)

    def test_weekly_summary_aggregates(self):
        history = SessionHistory(max_entries=10)
        history.record_if_improved(1, 100.0, 50.0, 80, 0, 2)
        history.record_if_improved(2, 90.0, 45.0, 85, 1, 2)
        summary = history.weekly_summary()
        self.assertEqual(summary["snapshot_count"], 2)
        self.assertEqual(summary["best_fitness"], 90.0)
        self.assertEqual(summary["worst_fitness"], 100.0)

    def test_trend_after_plateau(self):
        history = SessionHistory(max_entries=10)
        history.record_if_improved(1, 100.0, 50.0, 80, 0, 2)
        history.record_if_improved(5, 90.0, 45.0, 85, 0, 2)
        trend = history.trend(current_generation=10, current_fitness=90.0)
        self.assertEqual(trend["geracoes_desde_melhoria"], 5)
        self.assertAlmostEqual(trend["melhoria_fitness"], -10.0)


if __name__ == "__main__":
    unittest.main()
