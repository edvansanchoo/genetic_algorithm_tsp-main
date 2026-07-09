import unittest

from delivery_simulation.fuel.models import MAX_FUEL
from delivery_simulation.models import DEPOT_ID, DeliveryTask
from delivery_simulation.road_network import build_road_network
from delivery_simulation.route_evaluator import evaluate_permutation


class RouteEvaluatorTests(unittest.TestCase):
    def test_single_task_uses_graph_path(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "T1": (5.0, 0.0),
            "A": (10.0, 0.0),
        }
        network = build_road_network(nodes, radius=6.0)
        tasks = [DeliveryTask("A", 4)]
        distance, trips, report = evaluate_permutation(tasks, tasks, network)

        stop_ids = [stop.point_id for stop in trips[0].stops]
        self.assertIn("T1", stop_ids)
        self.assertAlmostEqual(distance, 20.0)
        self.assertTrue(report.is_feasible)

    def test_capacity_splits_into_two_trips(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (10.0, 0.0)}
        network = build_road_network(nodes, radius=100.0)
        tasks = [DeliveryTask("A", 10), DeliveryTask("A", 4)]
        distance, trips, report = evaluate_permutation(tasks, list(tasks), network)

        self.assertEqual(len(trips), 2)
        self.assertEqual(trips[0].stops[0].point_id, DEPOT_ID)
        self.assertEqual(trips[0].stops[-1].point_id, DEPOT_ID)
        self.assertEqual(trips[1].stops[-1].point_id, DEPOT_ID)
        self.assertGreater(distance, 0.0)
        self.assertTrue(report.is_feasible)

    def test_unreachable_leg_returns_infinity(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (100.0, 0.0)}
        network = build_road_network(nodes, radius=1.0)
        tasks = [DeliveryTask("A", 4)]
        distance, trips, report = evaluate_permutation(tasks, tasks, network)
        self.assertEqual(distance, float("inf"))
        self.assertEqual(trips, [])
        self.assertFalse(report.is_feasible)


class RouteEvaluatorFuelTests(unittest.TestCase):
    def test_insufficient_fuel_without_station_is_infinity(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (200.0, 0.0)}
        network = build_road_network(nodes, radius=250.0)
        tasks = [DeliveryTask("A", 4)]
        distance, trips, report = evaluate_permutation(tasks, tasks, network)
        self.assertEqual(distance, float("inf"))
        self.assertFalse(report.is_feasible)

    def test_station_detour_makes_long_leg_feasible(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "F1": (80.0, 0.0),
            "A": (160.0, 0.0),
            "F2": (140.0, 40.0),
        }
        network = build_road_network(nodes, radius=150.0)
        tasks = [DeliveryTask("A", 4)]
        distance, trips, report = evaluate_permutation(tasks, tasks, network)
        self.assertTrue(report.is_feasible)
        self.assertNotEqual(distance, float("inf"))
        stop_ids = [stop.point_id for stop in trips[0].stops]
        self.assertTrue("F1" in stop_ids or "F2" in stop_ids)
        self.assertTrue(any(stop.is_fuel_station for stop in trips[0].stops))
        self.assertLess(report.final_fuel, MAX_FUEL)
