"""Testes da malha hub estrita: hubs só via trânsito."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import (
    build_vrp_mesh,
    delivery_segment_path,
)
from traveling_salesman_problem.problem.road_network import (
    build_delivery_hub_network,
    find_path,
    find_path_weighted,
)
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryPoint


class DeliveryHubNetworkTests(unittest.TestCase):
    def test_no_hub_to_hub_edges(self) -> None:
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (0.0, 10.0),
            "T1": (5.0, 5.0),
        }
        network = build_delivery_hub_network(nodes, ["A", "B"])
        edge_set = {tuple(sorted(edge)) for edge in network.edges}
        self.assertNotIn(("A", "B"), edge_set)
        self.assertNotIn(tuple(sorted((DEPOT_ID, "A"))), edge_set)
        self.assertNotIn(tuple(sorted((DEPOT_ID, "B"))), edge_set)
        self.assertIn(tuple(sorted(("A", "T1"))), edge_set)
        self.assertIn(tuple(sorted((DEPOT_ID, "T1"))), edge_set)
        self.assertIn(tuple(sorted(("T1", "B"))), edge_set)

    def test_edge_count_formula_strict_hub(self) -> None:
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (1.0, 0.0),
            "B": (2.0, 0.0),
            "T1": (3.0, 0.0),
        }
        network = build_delivery_hub_network(nodes, ["A", "B"])
        self.assertEqual(len(network.edges), 3)


class DeliveryHubPathTests(unittest.TestCase):
    def _hub_network(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (20.0, 0.0),
            "T1": (10.0, 10.0),
        }
        return build_delivery_hub_network(nodes, ["A", "B"])

    def test_depot_to_delivery_uses_transit(self) -> None:
        network = self._hub_network()
        path = find_path(network, DEPOT_ID, "A")
        self.assertTrue(path)
        self.assertGreaterEqual(len(path), 3)
        self.assertIn("T1", path)
        self.assertEqual(path[0], DEPOT_ID)
        self.assertEqual(path[-1], "A")

    def test_delivery_to_depot_uses_transit(self) -> None:
        network = self._hub_network()
        path = find_path(network, "A", DEPOT_ID)
        self.assertTrue(path)
        self.assertIn("T1", path)

    def test_delivery_to_delivery_uses_transit_not_depot(self) -> None:
        network = self._hub_network()
        path = find_path_weighted(network, "A", "B", no_through={DEPOT_ID})
        self.assertTrue(path)
        self.assertIn("T1", path)
        self.assertNotIn(DEPOT_ID, path[1:-1])

    def test_delivery_to_delivery_empty_when_no_transit(self) -> None:
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (10.0, 0.0), "B": (20.0, 0.0)}
        network = build_delivery_hub_network(nodes, ["A", "B"])
        path = find_path(network, "A", "B", no_through={DEPOT_ID})
        self.assertEqual(path, [])


class VrpHubMeshIntegrationTests(unittest.TestCase):
    def test_vrp_mesh_delivery_paths_use_transit(self) -> None:
        depot = (0.0, 0.0)
        deliveries = [
            DeliveryPoint("A", (40.0, 0.0), priority=5, demand=3),
            DeliveryPoint("B", (0.0, 40.0), priority=7, demand=4),
        ]
        mesh = build_vrp_mesh(
            depot,
            deliveries,
            map_bounds=(-10, -10, 60, 60),
            transit_count=2,
            blocked_count=1,
            rng_seed=11,
        )
        path = delivery_segment_path(
            mesh,
            deliveries[0].coordinate,
            deliveries[1].coordinate,
        )
        self.assertTrue(path)
        self.assertTrue(set(mesh.transit_ids) & set(path))
        if DEPOT_ID in path:
            self.assertNotIn(DEPOT_ID, path[1:-1])


if __name__ == "__main__":
    unittest.main()
