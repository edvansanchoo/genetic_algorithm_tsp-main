"""Testes de fitness com distância na malha."""

import unittest

from traveling_salesman_problem.genetic_algorithm.fitness import (
    calculate_route_distance,
    calculate_route_fitness,
)
from traveling_salesman_problem.problem.delivery_mesh import (
    build_delivery_mesh,
    delivery_mesh_from_parts,
)
from traveling_salesman_problem.problem.road_network import RoadNetwork


class MeshFitnessTests(unittest.TestCase):
    def test_mesh_distance_is_finite_for_reachable_route(self):
        cities = [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)]
        mesh = build_delivery_mesh(
            cities,
            (-10, -10, 60, 60),
            transit_count=4,
            blocked_count=1,
            rng_seed=2,
        )
        mesh_dist = calculate_route_distance(list(cities), mesh=mesh)
        self.assertTrue(mesh_dist < float("inf"))

    def test_priority_still_added(self):
        cities = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        priorities = [5, 10, 1, 3]
        mesh = build_delivery_mesh(
            cities,
            (-5, -5, 15, 15),
            transit_count=2,
            blocked_count=1,
            rng_seed=3,
        )
        route = list(cities)
        distance = calculate_route_distance(route, mesh=mesh)
        fitness = calculate_route_fitness(
            route,
            city_coordinates=cities,
            priorities=priorities,
            priority_weight=2.0,
            mesh=mesh,
        )
        self.assertAlmostEqual(fitness, distance + 2.0 * 40)

    def test_infinite_when_no_path(self):
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
        )
        self.assertEqual(
            calculate_route_distance([(0.0, 0.0), (100.0, 0.0)], mesh=mesh),
            float("inf"),
        )


if __name__ == "__main__":
    unittest.main()
