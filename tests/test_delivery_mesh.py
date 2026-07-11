"""Testes da malha nativa e do pathfinding."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import (
    build_delivery_mesh,
    deliveries_mutually_reachable,
    delivery_mesh_from_parts,
    delivery_segment_distance,
    delivery_segment_path,
    effective_transit_count,
    expand_route_polyline,
)
from traveling_salesman_problem.problem.vrp_models import DeliveryPoint
from traveling_salesman_problem.problem.road_network import (
    RoadNetwork,
    build_radius_graph,
    build_road_network,
    find_path,
    path_distance,
)


class RoadNetworkTests(unittest.TestCase):
    def test_build_radius_graph_only_connects_within_radius(self):
        nodes = {
            "D0": (0.0, 0.0),
            "D1": (5.0, 0.0),
            "D2": (20.0, 0.0),
        }
        edges = build_radius_graph(nodes, radius=10.0)
        self.assertIn(("D0", "D1"), edges)
        self.assertNotIn(("D0", "D2"), edges)
        self.assertNotIn(("D1", "D2"), edges)

    def test_find_path_goes_through_transit(self):
        nodes = {
            "D0": (0.0, 0.0),
            "T1": (5.0, 0.0),
            "D1": (10.0, 0.0),
        }
        network = build_road_network(nodes, radius=6.0)
        path = find_path(network, "D0", "D1", set())
        self.assertEqual(path, ["D0", "T1", "D1"])

    def test_find_path_skips_blocked_destination(self):
        nodes = {"D0": (0.0, 0.0), "D1": (5.0, 0.0)}
        network = build_road_network(nodes, radius=10.0)
        self.assertEqual(find_path(network, "D0", "D1", {"D1"}), [])

    def test_path_distance_sums_segments(self):
        nodes = {"D0": (0.0, 0.0), "D1": (3.0, 4.0)}
        network = build_road_network(nodes, radius=10.0)
        self.assertAlmostEqual(path_distance(network, ["D0", "D1"]), 5.0)

    def test_build_complete_graph_connects_all_pairs(self):
        from traveling_salesman_problem.problem.road_network import build_complete_graph

        nodes = {
            "D0": (0.0, 0.0),
            "D1": (5.0, 0.0),
            "T1": (2.0, 3.0),
            "T2": (8.0, 1.0),
        }
        edges = build_complete_graph(nodes)
        self.assertEqual(len(edges), 6)
        edge_set = {tuple(sorted(pair)) for pair in edges}
        self.assertIn(("D0", "D1"), edge_set)
        self.assertIn(("D0", "T2"), edge_set)
        self.assertIn(("T1", "T2"), edge_set)

    def test_build_complete_network_has_zero_radius(self):
        from traveling_salesman_problem.problem.road_network import build_complete_network

        nodes = {"A": (0.0, 0.0), "B": (100.0, 0.0)}
        network = build_complete_network(nodes)
        self.assertEqual(len(network.edges), 1)
        self.assertEqual(network.connection_radius, 0.0)


class DeliveryMeshTests(unittest.TestCase):
    def test_blocked_node_never_on_path(self):
        cities = [(0.0, 0.0), (100.0, 0.0)]
        mesh = build_delivery_mesh(
            cities,
            map_bounds=(-20, -20, 120, 120),
            transit_count=4,
            blocked_count=1,
            rng_seed=1,
        )
        path = delivery_segment_path(mesh, cities[0], cities[1])
        self.assertTrue(path)
        for blocked_id in mesh.blocked_ids:
            self.assertNotIn(blocked_id, path)
            self.assertNotIn(blocked_id, mesh.network.nodes)

    def test_distance_infinite_when_disconnected(self):
        network = RoadNetwork(
            nodes={"D0": (0.0, 0.0), "D1": (100.0, 0.0)},
            edges=[],
            connection_radius=10.0,
        )
        mesh = delivery_mesh_from_parts(
            network,
            delivery_ids=["D0", "D1"],
            transit_ids=[],
            blocked_ids={"B1"},
            blocked_coordinates={"B1": (50.0, 0.0)},
        )
        self.assertEqual(
            delivery_segment_distance(mesh, (0.0, 0.0), (100.0, 0.0)),
            float("inf"),
        )
        self.assertFalse(deliveries_mutually_reachable(mesh))

    def test_path_detours_via_transit(self):
        network = RoadNetwork(
            nodes={
                "D0": (0.0, 0.0),
                "T1": (50.0, 40.0),
                "D1": (100.0, 0.0),
            },
            edges=[("D0", "T1"), ("T1", "D1")],
            connection_radius=70.0,
        )
        mesh = delivery_mesh_from_parts(
            network,
            delivery_ids=["D0", "D1"],
            transit_ids=["T1"],
            blocked_ids={"B1"},
            blocked_coordinates={"B1": (50.0, 0.0)},
        )
        path = delivery_segment_path(mesh, (0.0, 0.0), (100.0, 0.0))
        self.assertEqual(path, ["D0", "T1", "D1"])
        self.assertNotIn("B1", path)

    def test_expand_route_polyline_includes_transit_coords(self):
        network = RoadNetwork(
            nodes={
                "D0": (0.0, 0.0),
                "T1": (50.0, 40.0),
                "D1": (100.0, 0.0),
            },
            edges=[("D0", "T1"), ("T1", "D1")],
            connection_radius=70.0,
        )
        mesh = delivery_mesh_from_parts(
            network,
            delivery_ids=["D0", "D1"],
            transit_ids=["T1"],
            blocked_ids={"B1"},
            blocked_coordinates={"B1": (50.0, 0.0)},
        )
        polyline = expand_route_polyline(mesh, [(0.0, 0.0), (100.0, 0.0)])
        self.assertIn((50.0, 40.0), polyline)
        self.assertGreaterEqual(len(polyline), 3)

    def test_generated_mesh_is_hub_graph(self):
        cities = [(0.0, 0.0), (100.0, 0.0), (50.0, 80.0)]
        mesh = build_delivery_mesh(
            cities,
            map_bounds=(-20, -20, 120, 120),
            transit_count=4,
            blocked_count=1,
            rng_seed=1,
        )
        node_count = len(mesh.network.nodes)
        delivery_count = len(mesh.delivery_ids)
        expected_edges = (
            node_count * (node_count - 1) // 2
            - delivery_count * (delivery_count - 1) // 2
        )
        self.assertEqual(len(mesh.network.edges), expected_edges)
        delivery_edge_set = {
            tuple(sorted((node_a, node_b)))
            for node_a, node_b in mesh.network.edges
            if node_a in mesh.delivery_ids and node_b in mesh.delivery_ids
        }
        self.assertEqual(delivery_edge_set, set())

    def test_blocked_not_in_network_nodes(self):
        cities = [(0.0, 0.0), (100.0, 0.0)]
        mesh = build_delivery_mesh(
            cities,
            map_bounds=(-20, -20, 120, 120),
            transit_count=2,
            blocked_count=2,
            rng_seed=3,
        )
        for blocked_id in mesh.blocked_ids:
            self.assertNotIn(blocked_id, mesh.network.nodes)


class EffectiveTransitCountTests(unittest.TestCase):
    def test_single_vehicle_margin_is_plus_ten(self):
        deliveries = [
            DeliveryPoint("A", (10.0, 0.0), priority=5, demand=10),
            DeliveryPoint("B", (20.0, 0.0), priority=7, demand=10),
        ]
        effective = effective_transit_count(
            deliveries,
            vehicle_count=1,
            capacity=10,
            requested_transit=5,
            maximum_transit=30,
        )
        self.assertEqual(effective, 12)

    def test_single_vehicle_requires_more_transit_than_slider_minimum(self):
        deliveries = [
            DeliveryPoint("A", (10.0, 0.0), priority=5, demand=12),
            DeliveryPoint("B", (20.0, 0.0), priority=7, demand=12),
        ]
        effective = effective_transit_count(
            deliveries,
            vehicle_count=1,
            capacity=10,
            requested_transit=5,
            maximum_transit=20,
        )
        self.assertGreater(effective, 5)

    def test_many_vehicles_applies_minimum_margin(self):
        deliveries = [
            DeliveryPoint("A", (10.0, 0.0), priority=5, demand=3),
            DeliveryPoint("B", (20.0, 0.0), priority=7, demand=3),
        ]
        effective = effective_transit_count(
            deliveries,
            vehicle_count=3,
            capacity=10,
            requested_transit=8,
            maximum_transit=20,
        )
        self.assertEqual(effective, 11)

    def test_many_vehicles_respects_requested_transit_when_above_minimum(self):
        deliveries = [
            DeliveryPoint("A", (10.0, 0.0), priority=5, demand=3),
            DeliveryPoint("B", (20.0, 0.0), priority=7, demand=3),
        ]
        effective = effective_transit_count(
            deliveries,
            vehicle_count=3,
            capacity=10,
            requested_transit=15,
            maximum_transit=20,
        )
        self.assertEqual(effective, 15)

    def test_single_vehicle_many_tokens_uses_full_margin(self):
        deliveries = [
            DeliveryPoint(f"P{index}", (float(index), 0.0), priority=5, demand=12)
            for index in range(12)
        ]
        effective = effective_transit_count(
            deliveries,
            vehicle_count=1,
            capacity=10,
            requested_transit=8,
            maximum_transit=40,
        )
        self.assertEqual(effective, 34)


class StrictVrpMeshTests(unittest.TestCase):
    def test_build_vrp_mesh_reachable_with_strict_hub(self):
        from traveling_salesman_problem.problem.delivery_mesh import (
            build_vrp_mesh,
            depot_reaches_all_deliveries,
        )

        depot = (400.0, 300.0)
        deliveries = [
            DeliveryPoint(f"P{i}", (100.0 + i * 40, 200.0), priority=5, demand=5)
            for i in range(12)
        ]
        mesh = build_vrp_mesh(
            depot,
            deliveries,
            map_bounds=(0, 0, 800, 600),
            transit_count=8,
            blocked_count=2,
            rng_seed=7,
            maximum_transit=20,
        )
        self.assertTrue(depot_reaches_all_deliveries(mesh))
        path = delivery_segment_path(mesh, depot, deliveries[0].coordinate)
        self.assertGreaterEqual(len(path), 3)
        self.assertTrue(set(mesh.transit_ids) & set(path))


class VrpMeshTests(unittest.TestCase):
    def test_build_vrp_mesh_includes_depot(self):
        from traveling_salesman_problem.problem.delivery_mesh import build_vrp_mesh
        from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryPoint

        depot = (0.0, 0.0)
        deliveries = [
            DeliveryPoint("A", (40.0, 0.0), priority=5, demand=3),
            DeliveryPoint("B", (0.0, 40.0), priority=7, demand=4),
        ]
        mesh = build_vrp_mesh(
            depot,
            deliveries,
            map_bounds=(-10, -10, 60, 60),
            transit_count=3,
            blocked_count=1,
            rng_seed=11,
        )
        self.assertIn(DEPOT_ID, mesh.network.nodes)
        self.assertIn("A", mesh.network.nodes)
        self.assertIn("B", mesh.network.nodes)
        node_count = len(mesh.network.nodes)
        delivery_count = len(mesh.delivery_ids)
        hub_count = 1 + delivery_count
        self.assertEqual(
            len(mesh.network.edges),
            node_count * (node_count - 1) // 2
            - hub_count * (hub_count - 1) // 2,
        )
        path = delivery_segment_path(mesh, depot, deliveries[0].coordinate)
        self.assertTrue(path)
        self.assertEqual(path[0], DEPOT_ID)
        self.assertGreaterEqual(len(path), 3)
        self.assertTrue(set(mesh.transit_ids) & set(path))


if __name__ == "__main__":
    unittest.main()
