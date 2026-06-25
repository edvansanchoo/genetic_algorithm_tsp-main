import unittest

from traveling_salesman_problem.problem.city_generator import generate_random_priorities
from traveling_salesman_problem.problem.priority_presets import apply_hospital_priority_preset


class HospitalPresetTests(unittest.TestCase):
    def test_preset_is_reproducible_for_same_city_count(self):
        first = apply_hospital_priority_preset(15)
        second = apply_hospital_priority_preset(15)
        self.assertEqual(first, second)

    def test_preset_values_in_valid_range(self):
        priorities = apply_hospital_priority_preset(15)
        self.assertEqual(len(priorities), 15)
        self.assertTrue(all(1 <= value <= 10 for value in priorities))

    def test_preset_has_at_least_one_critical_delivery(self):
        priorities = apply_hospital_priority_preset(15)
        self.assertGreaterEqual(max(priorities), 8)

    def test_random_priorities_length_and_range(self):
        priorities = generate_random_priorities(15)
        self.assertEqual(len(priorities), 15)
        self.assertTrue(all(1 <= value <= 10 for value in priorities))
