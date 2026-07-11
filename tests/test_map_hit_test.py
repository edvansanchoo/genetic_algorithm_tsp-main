"""Testes de hit-test no mapa."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import (
    build_delivery_mesh,
    toggle_node_blocked,
)
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryPoint
from traveling_salesman_problem.visualization.map_hit_test import hit_test_map_node


class MapHitTestTests(unittest.TestCase):
    def test_hits_blocked_node_for_unblock(self):
        cities = [(0.0, 0.0), (100.0, 0.0)]
        mesh = build_delivery_mesh(
            cities,
            map_bounds=(-20, -20, 120, 120),
            transit_count=3,
            rng_seed=2,
        )
        transit_id = mesh.transit_ids[0]
        mesh = toggle_node_blocked(mesh, transit_id, mesh.delivery_ids)
        coord = mesh.blocked_coordinates[transit_id]
        hit = hit_test_map_node(mesh, None, [], (int(coord[0]), int(coord[1])), 12.0)
        self.assertEqual(hit, transit_id)

    def test_hits_depot_before_transit(self):
        depot = (50.0, 50.0)
        deliveries = [DeliveryPoint("A", (200.0, 200.0), 5, 3)]
        mesh = build_delivery_mesh(
            [deliveries[0].coordinate],
            map_bounds=(-20, -20, 250, 250),
            transit_count=2,
            rng_seed=4,
        )
        hit = hit_test_map_node(mesh, depot, deliveries, (50, 50), 12.0)
        self.assertEqual(hit, DEPOT_ID)

    def test_returns_none_when_far(self):
        mesh = build_delivery_mesh(
            [(0.0, 0.0)],
            map_bounds=(-20, -20, 120, 120),
            transit_count=2,
            rng_seed=1,
        )
        self.assertIsNone(hit_test_map_node(mesh, None, [], (999, 999), 12.0))


if __name__ == "__main__":
    unittest.main()
