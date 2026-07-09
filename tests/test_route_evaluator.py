import unittest

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
        distance, trips = evaluate_permutation(tasks, tasks, network)

        stop_ids = [stop.point_id for stop in trips[0].stops]
        self.assertIn("T1", stop_ids)
        self.assertAlmostEqual(distance, 20.0)

    def test_capacity_splits_into_two_trips(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (10.0, 0.0)}
        network = build_road_network(nodes, radius=100.0)
        tasks = [DeliveryTask("A", 10), DeliveryTask("A", 4)]
        distance, trips = evaluate_permutation(tasks, list(tasks), network)

        self.assertEqual(len(trips), 2)
        self.assertEqual(trips[0].stops[0].point_id, DEPOT_ID)
        self.assertEqual(trips[0].stops[-1].point_id, DEPOT_ID)
        self.assertEqual(trips[1].stops[-1].point_id, DEPOT_ID)
        self.assertGreater(distance, 0.0)

    def test_unreachable_leg_returns_infinity(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (100.0, 0.0)}
        network = build_road_network(nodes, radius=1.0)
        tasks = [DeliveryTask("A", 4)]
        distance, trips = evaluate_permutation(tasks, tasks, network)
        self.assertEqual(distance, float("inf"))
        self.assertEqual(trips, [])
