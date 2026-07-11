"""Testes dos controles headless para o modo Web."""

import unittest

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.headless_controls import (
    HeadlessButton,
    HeadlessSlider,
    HeadlessToggle,
)


class HeadlessControlsTests(unittest.TestCase):
    def test_headless_slider_integer_value_rounds(self):
        slider = HeadlessSlider(
            value=2.6,
            minimum_value=1.0,
            maximum_value=5.0,
            label="Veículos",
        )
        self.assertEqual(slider.integer_value, 3)

    def test_headless_slider_clamps_on_set(self):
        slider = HeadlessSlider(
            value=0.5,
            minimum_value=0.0,
            maximum_value=1.0,
            label="Mutação",
        )
        slider.value = 1.5
        self.assertEqual(slider.value, 1.0)

    def test_headless_toggle_defaults_inactive(self):
        toggle = HeadlessToggle(label="2-opt", is_active=False)
        self.assertFalse(toggle.is_active)
        toggle.is_active = True
        self.assertTrue(toggle.is_active)

    def test_headless_button_defaults(self):
        button = HeadlessButton(label="Sortear posições")
        self.assertEqual(button.subtitle, "")
        self.assertFalse(button.was_pressed)


class HeadlessSimulationStateTests(unittest.TestCase):
    def test_initialize_headless_creates_controls_without_pygame_widgets(self):
        simulation = SimulationState(settings=ApplicationSettings())
        simulation.initialize_headless()
        self.assertIsNotNone(simulation.mutation_slider)
        self.assertIsInstance(simulation.mutation_slider, HeadlessSlider)
        self.assertIsNotNone(simulation.depot)
        self.assertGreater(len(simulation.deliveries), 0)
        self.assertGreater(len(simulation.vehicle_states), 0)

    def test_restart_vehicle_genetic_resets_generation_counter(self):
        simulation = SimulationState(settings=ApplicationSettings())
        simulation.initialize_headless()
        simulation.run_one_generation()
        second_gen, *_ = simulation.run_one_generation()
        self.assertEqual(second_gen, 2)
        simulation.restart_vehicle_genetic()
        first_after_restart, *_ = simulation.run_one_generation()
        self.assertEqual(first_after_restart, 1)


if __name__ == "__main__":
    unittest.main()
