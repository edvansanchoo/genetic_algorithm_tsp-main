"""Testes de limite dinâmico do slider de capacidade."""

import unittest
from unittest.mock import MagicMock

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.problem.vrp_assignment import total_delivery_demand
from traveling_salesman_problem.problem.vrp_models import DeliveryPoint
from traveling_salesman_problem.simulation.simulation_state import SimulationState


class TotalDeliveryDemandTests(unittest.TestCase):
    def test_sums_all_demands(self) -> None:
        deliveries = [
            DeliveryPoint("A", (0.0, 0.0), priority=5, demand=6),
            DeliveryPoint("B", (10.0, 0.0), priority=3, demand=4),
            DeliveryPoint("C", (5.0, 5.0), priority=1, demand=10),
        ]
        self.assertEqual(total_delivery_demand(deliveries), 20)

    def test_empty_returns_zero(self) -> None:
        self.assertEqual(total_delivery_demand([]), 0)


class CapacitySliderSyncTests(unittest.TestCase):
    def _state_with_deliveries(self, demands: list[int]) -> SimulationState:
        state = SimulationState(settings=ApplicationSettings())
        state.deliveries = [
            DeliveryPoint(f"P{i}", (float(i), 0.0), priority=5, demand=demand)
            for i, demand in enumerate(demands)
        ]
        state.capacity_slider = MagicMock()
        state.capacity_slider.integer_value = 10
        state.capacity_slider.value = 10.0
        state.capacity_slider.maximum_value = 30.0
        return state

    def test_sync_sets_max_to_total_demand(self) -> None:
        state = self._state_with_deliveries([6, 4, 10])
        state._sync_capacity_slider_bounds()
        self.assertEqual(state.capacity_slider.maximum_value, 20.0)

    def test_sync_clamps_when_above_new_max(self) -> None:
        state = self._state_with_deliveries([3, 2])
        state.capacity_slider.integer_value = 80
        state.capacity_slider.value = 80.0
        state._sync_capacity_slider_bounds()
        self.assertEqual(state.capacity_slider.maximum_value, 5.0)
        self.assertEqual(state.capacity_slider.value, 5.0)

    def test_sync_keeps_value_when_below_max(self) -> None:
        state = self._state_with_deliveries([20, 30])
        state.capacity_slider.integer_value = 10
        state.capacity_slider.value = 10.0
        state._sync_capacity_slider_bounds()
        self.assertEqual(state.capacity_slider.maximum_value, 50.0)
        self.assertEqual(state.capacity_slider.value, 10.0)


if __name__ == "__main__":
    unittest.main()
