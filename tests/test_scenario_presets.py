import unittest
from unittest.mock import patch

from traveling_salesman_problem.genetic_algorithm.predefined_problems import (
    SCENARIO_PRESETS,
    get_scenario_city_count,
    get_scenario_coordinates,
    predefined_city_problems,
)
from traveling_salesman_problem.genetic_algorithm.selection import evolve_next_generation


class ScenarioPresetTests(unittest.TestCase):
    def test_all_expected_presets_exist(self):
        expected_ids = {
            "random",
            "small_5",
            "medium_10",
            "large_12",
            "extra_15",
            "intense_20",
            "advanced_25",
            "complex_30",
            "massive_40",
            "maximum_50",
        }
        self.assertEqual(set(SCENARIO_PRESETS.keys()), expected_ids)

    def test_random_preset_has_no_fixed_coordinates(self):
        preset = SCENARIO_PRESETS["random"]
        self.assertIsNone(preset.city_count)
        self.assertIsNone(preset.coordinates)

    def test_small_5_has_five_fixed_coordinates(self):
        coordinates = get_scenario_coordinates("small_5")
        self.assertIsNotNone(coordinates)
        self.assertEqual(len(coordinates), 5)

    def test_maximum_50_has_fifty_fixed_coordinates(self):
        coordinates = get_scenario_coordinates("maximum_50")
        self.assertIsNotNone(coordinates)
        self.assertEqual(len(coordinates), 50)

    def test_large_presets_are_reproducible(self):
        first = get_scenario_coordinates("massive_40")
        second = get_scenario_coordinates("massive_40")
        self.assertEqual(first, second)

    def test_get_scenario_city_count_uses_default_for_random(self):
        self.assertEqual(get_scenario_city_count("random", default=15), 15)

    def test_get_scenario_city_count_for_fixed_preset(self):
        self.assertEqual(get_scenario_city_count("medium_10", default=15), 10)

    def test_predefined_city_problems_backward_compat(self):
        self.assertEqual(len(predefined_city_problems[5]), 5)
        self.assertEqual(len(predefined_city_problems[15]), 15)


class TwoOptToggleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cities = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.population = [
            list(self.cities),
            [(0, 0), (10, 10), (10, 0), (0, 10)],
        ]
        self.fitness_values = [100.0, 200.0]

    @patch("traveling_salesman_problem.genetic_algorithm.selection.add_2opt")
    def test_use_2opt_true_calls_add_2opt(self, mock_add_2opt):
        mock_add_2opt.side_effect = lambda route: route
        evolve_next_generation(
            self.population,
            self.fitness_values,
            population_size=2,
            mutation_probability=0.0,
            use_2opt=True,
        )
        self.assertGreater(mock_add_2opt.call_count, 0)

    @patch("traveling_salesman_problem.genetic_algorithm.selection.add_2opt")
    def test_use_2opt_false_skips_add_2opt(self, mock_add_2opt):
        evolve_next_generation(
            self.population,
            self.fitness_values,
            population_size=2,
            mutation_probability=0.0,
            use_2opt=False,
        )
        mock_add_2opt.assert_not_called()
