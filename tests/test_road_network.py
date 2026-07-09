import unittest

from delivery_simulation.models import DEPOT_ID
from delivery_simulation.road_network import (
    build_radius_graph,
    build_road_network,
    find_path,
    path_distance,
    ensure_connectivity,
)


class RoadNetworkTests(unittest.TestCase):
    def test_build_radius_graph_only_connects_within_radius(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (5.0, 0.0),
            "B": (100.0, 0.0),
        }
        edges = build_radius_graph(nodes, radius=10.0)
        self.assertIn((DEPOT_ID, "A"), edges)
        self.assertNotIn((DEPOT_ID, "B"), edges)
        self.assertNotIn(("A", "B"), edges)

    def test_find_path_goes_through_transit(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "T1": (5.0, 0.0),
            "A": (10.0, 0.0),
        }
        network = build_road_network(nodes, radius=6.0)
        path = find_path(network, DEPOT_ID, "A", set())
        self.assertEqual(path, [DEPOT_ID, "T1", "A"])

    def test_find_path_respects_blocked_nodes(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "T1": (5.0, 0.0),
            "T2": (5.0, 5.0),
            "A": (10.0, 0.0),
        }
        network = build_road_network(nodes, radius=6.0)
        path = find_path(network, DEPOT_ID, "A", {"T1"})
        self.assertNotIn("T1", path)

    def test_path_distance_sums_segments(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (3.0, 4.0)}
        network = build_road_network(nodes, radius=10.0)
        self.assertAlmostEqual(path_distance(network, [DEPOT_ID, "A"]), 5.0)

    def test_ensure_connectivity(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (5.0, 0.0), "B": (10.0, 0.0)}
        network = build_road_network(nodes, radius=6.0)
        self.assertTrue(ensure_connectivity(network, DEPOT_ID, ["A", "B"]))
