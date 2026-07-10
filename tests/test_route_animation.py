"""Testes da polyline de animação VRP."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import delivery_mesh_from_parts
from traveling_salesman_problem.problem.road_network import RoadNetwork
from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, Trip, TripStop
from traveling_salesman_problem.visualization.route_animation import (
    build_animation_polyline,
    point_along_polyline,
)


class RouteAnimationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.depot = (0.0, 0.0)
        network = RoadNetwork(
            nodes={DEPOT_ID: (0.0, 0.0), "A": (10.0, 0.0)},
            edges=[(DEPOT_ID, "A")],
            connection_radius=15.0,
        )
        self.mesh = delivery_mesh_from_parts(
            network,
            delivery_ids=["A"],
            transit_ids=[],
        )
        self.plan = DecodedVehiclePlan(
            trips=[
                Trip(
                    stops=[
                        TripStop(DEPOT_ID, 0, self.depot),
                        TripStop("A", 3, (10.0, 0.0)),
                        TripStop(DEPOT_ID, 0, self.depot),
                    ],
                    distance=20.0,
                    path_node_ids=[[DEPOT_ID, "A"], ["A", DEPOT_ID]],
                )
            ],
            total_distance=20.0,
            priority_penalty=0.0,
            fitness=20.0,
        )

    def test_polyline_starts_and_ends_at_depot(self):
        points = build_animation_polyline(self.mesh, self.plan)
        self.assertGreaterEqual(len(points), 2)
        self.assertEqual(points[0], self.depot)
        self.assertEqual(points[-1], self.depot)

    def test_point_along_polyline_endpoints(self):
        points = [(0.0, 0.0), (10.0, 0.0), (0.0, 0.0)]
        self.assertEqual(point_along_polyline(points, 0.0), (0.0, 0.0))
        end = point_along_polyline(points, 0.999)
        self.assertAlmostEqual(end[0], 0.0, places=1)


if __name__ == "__main__":
    unittest.main()
