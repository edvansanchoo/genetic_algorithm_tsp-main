import unittest

from traveling_salesman_problem.genetic_algorithm.fitness import (
    build_delivery_visit_order,
    calculate_priority_penalty,
    calculate_route_distance,
    calculate_route_fitness,
    decompose_route_fitness,
)
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


class PriorityPenaltyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.city_coordinates = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.priorities = [5, 10, 1, 3]

    def test_priority_penalty_rotates_from_reference_city(self):
        route = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertEqual(
            calculate_priority_penalty(route, self.city_coordinates, self.priorities),
            40,
        )

    def test_priority_penalty_ignores_rotation_start_in_route_list(self):
        route = [(10, 0), (10, 10), (0, 10), (0, 0)]
        self.assertEqual(
            calculate_priority_penalty(route, self.city_coordinates, self.priorities),
            40,
        )

    def test_fitness_with_zero_weight_ignores_priority(self):
        route = [(10, 0), (10, 10), (0, 10), (0, 0)]
        without_priority = calculate_route_fitness(route)
        with_priority = calculate_route_fitness(
            route,
            city_coordinates=self.city_coordinates,
            priorities=self.priorities,
            priority_weight=0.0,
        )
        self.assertEqual(without_priority, with_priority)

    def test_fitness_adds_weighted_priority_penalty(self):
        route = [(0, 0), (10, 0), (10, 10), (0, 10)]
        distance = calculate_route_distance(route)
        fitness = calculate_route_fitness(
            route,
            city_coordinates=self.city_coordinates,
            priorities=self.priorities,
            priority_weight=2.0,
        )
        self.assertAlmostEqual(fitness, distance + 2.0 * 40)

    def test_decompose_route_fitness_returns_components(self):
        route = [(0, 0), (10, 0), (10, 10), (0, 10)]
        total, distance, weighted_priority = decompose_route_fitness(
            route,
            city_coordinates=self.city_coordinates,
            priorities=self.priorities,
            priority_weight=2.0,
        )
        self.assertAlmostEqual(distance, calculate_route_distance(route))
        self.assertAlmostEqual(weighted_priority, 80.0)
        self.assertAlmostEqual(total, distance + 80.0)

    def test_build_delivery_visit_order(self):
        route = [(10, 0), (10, 10), (0, 10), (0, 0)]
        visit_order = build_delivery_visit_order(
            route,
            self.city_coordinates,
            self.priorities,
        )
        self.assertEqual(
            visit_order,
            [(1, 1, 5), (2, 2, 10), (3, 3, 1), (4, 4, 3)],
        )
