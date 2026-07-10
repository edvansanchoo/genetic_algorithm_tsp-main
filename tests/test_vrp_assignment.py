"""Testes de modelos VRP, tokens e atribuição gulosa."""

import unittest

from traveling_salesman_problem.problem.vrp_assignment import (
    assign_deliveries_greedy,
    split_into_tokens,
)
from traveling_salesman_problem.problem.vrp_models import DeliveryPoint


class SplitIntoTokensTests(unittest.TestCase):
    def test_split_demand_exceeds_capacity(self):
        point = DeliveryPoint("A", (0.0, 0.0), priority=8, demand=14)
        tokens = split_into_tokens(point, capacity=10)
        self.assertEqual(
            [(token.point_id, token.quantity) for token in tokens],
            [("A", 10), ("A", 4)],
        )
        self.assertTrue(all(token.priority == 8 for token in tokens))

    def test_split_demand_fits_in_one_token(self):
        point = DeliveryPoint("B", (1.0, 1.0), priority=3, demand=7)
        tokens = split_into_tokens(point, capacity=10)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].quantity, 7)


class AssignDeliveriesGreedyTests(unittest.TestCase):
    def test_assign_balances_load_and_covers_all(self):
        depot = (0.0, 0.0)
        deliveries = [
            DeliveryPoint("A", (1.0, 0.0), 5, 6),
            DeliveryPoint("B", (2.0, 0.0), 5, 8),
            DeliveryPoint("C", (3.0, 0.0), 5, 2),
        ]
        assignment = assign_deliveries_greedy(
            deliveries,
            vehicle_count=2,
            depot=depot,
        )
        self.assertEqual(set(assignment), {0, 1})
        assigned_ids = {point.id for points in assignment.values() for point in points}
        self.assertEqual(assigned_ids, {"A", "B", "C"})
        loads = {
            vehicle_id: sum(point.demand for point in points)
            for vehicle_id, points in assignment.items()
        }
        self.assertLessEqual(
            abs(loads[0] - loads[1]),
            max(point.demand for point in deliveries),
        )

    def test_assign_returns_all_vehicle_keys(self):
        depot = (0.0, 0.0)
        deliveries = [DeliveryPoint("A", (1.0, 0.0), 1, 1)]
        assignment = assign_deliveries_greedy(deliveries, vehicle_count=3, depot=depot)
        self.assertEqual(set(assignment), {0, 1, 2})


if __name__ == "__main__":
    unittest.main()
