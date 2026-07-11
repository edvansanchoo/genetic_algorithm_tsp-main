"""Testes do painel de rotas VRP."""

import unittest

from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, Trip, TripStop
from traveling_salesman_problem.visualization.route_panel import (
    build_route_panel_rows,
    filter_plans_by_focus,
    format_trip_line,
    format_vehicle_section,
    hit_test_route_panel,
)


def _trip(*node_quantities):
    stops = [
        TripStop(node_id=node_id, quantity=qty, coordinate=(0.0, 0.0))
        for node_id, qty in node_quantities
    ]
    return Trip(stops=stops, distance=10.0, path_node_ids=[])


class RoutePanelTests(unittest.TestCase):
    def test_format_trip_starts_and_ends_with_d(self):
        trip = _trip((DEPOT_ID, 0), ("A", 5), ("C", 4), (DEPOT_ID, 0))
        line = format_trip_line(trip, trip_index=1, capacity=10)
        self.assertTrue(line.startswith("Viagem 1: D →"))
        self.assertIn("→ D  (9/10)", line)

    def test_format_vehicle_section(self):
        plan = DecodedVehiclePlan(
            trips=[
                _trip((DEPOT_ID, 0), ("A", 5), (DEPOT_ID, 0)),
                _trip((DEPOT_ID, 0), ("B", 4), (DEPOT_ID, 0)),
            ],
            total_distance=20.0,
            priority_penalty=0.0,
            fitness=20.0,
        )
        lines = format_vehicle_section(0, plan, capacity=10)
        self.assertEqual(lines[0], "Veículo 1")
        self.assertIn("D → A → D", lines[1])
        self.assertIn("D → B → D", lines[2])

    def test_filter_plans_by_focus(self):
        plans = {
            0: DecodedVehiclePlan([], 1.0, 0.0, 1.0),
            1: DecodedVehiclePlan([], 2.0, 0.0, 2.0),
        }
        self.assertEqual(set(filter_plans_by_focus(plans, None)), {0, 1})
        self.assertEqual(set(filter_plans_by_focus(plans, 1)), {1})
        self.assertEqual(filter_plans_by_focus(plans, 9), {})

    def test_hit_test_trip_row(self):
        plan = DecodedVehiclePlan(
            trips=[_trip((DEPOT_ID, 0), ("A", 5), (DEPOT_ID, 0))],
            total_distance=10.0,
            priority_penalty=0.0,
            fitness=10.0,
        )
        rows = build_route_panel_rows({0: plan}, capacity=10)
        hit = hit_test_route_panel(rows, 20, 42, 12, 26, 400)
        self.assertEqual(hit, ("trip", 0, 0))


if __name__ == "__main__":
    unittest.main()
