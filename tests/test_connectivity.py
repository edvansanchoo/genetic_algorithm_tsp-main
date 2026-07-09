import random
import unittest

from delivery_simulation.models import DEPOT_ID
from delivery_simulation.road_network import (
    build_connected_network,
    build_road_network,
    ensure_connectivity,
    generate_transit_nodes,
)


class ConnectivityTests(unittest.TestCase):
    def test_generate_transit_and_build_connected_network(self):
        nodes = {DEPOT_ID: (100.0, 100.0), "A": (200.0, 200.0)}
        transit = generate_transit_nodes(
            5, 50, 50, 400, 400, rng=random.Random(1)
        )
        for node in transit:
            nodes[node.id] = node.coordinate

        network, warning = build_connected_network(nodes, 150.0, DEPOT_ID, ["A"])
        self.assertTrue(ensure_connectivity(network, DEPOT_ID, ["A"]))

    def test_all_delivery_points_reachable_after_fallback(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (100.0, 0.0), "B": (0.0, 100.0)}
        network = build_road_network(nodes, radius=10.0)
        self.assertFalse(ensure_connectivity(network, DEPOT_ID, ["A", "B"]))

        connected, warning = build_connected_network(nodes, 10.0, DEPOT_ID, ["A", "B"], max_attempts=1)
        self.assertTrue(ensure_connectivity(connected, DEPOT_ID, ["A", "B"]))
        self.assertIsNotNone(warning)
