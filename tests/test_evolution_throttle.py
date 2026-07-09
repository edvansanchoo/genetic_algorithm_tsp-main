import unittest

from traveling_salesman_problem.simulation.evolution_throttle import compute_generations_for_frame


class EvolutionThrottleTests(unittest.TestCase):
    def test_three_per_second_over_one_second(self):
        count, remaining = compute_generations_for_frame(1.0, 3.0, 0.0)
        self.assertEqual(count, 3)
        self.assertAlmostEqual(remaining, 0.0)

    def test_accumulates_partial_frames(self):
        count, remaining = compute_generations_for_frame(0.1, 3.0, 0.0)
        self.assertEqual(count, 0)
        self.assertAlmostEqual(remaining, 0.1)

        count, remaining = compute_generations_for_frame(0.1, 3.0, remaining)
        self.assertEqual(count, 0)
        self.assertAlmostEqual(remaining, 0.2)
