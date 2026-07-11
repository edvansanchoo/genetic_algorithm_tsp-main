"""Decoder VRP com diversificação de arestas (ida ≠ volta)."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import delivery_mesh_from_parts
from traveling_salesman_problem.problem.road_network import RoadNetwork
from traveling_salesman_problem.problem.vrp_decoder import decode_vehicle_permutation
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryToken


def _diamond_mesh():
    network = RoadNetwork(
        nodes={
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (10.0, 10.0),
            "X": (20.0, 0.0),
        },
        edges=[
            (DEPOT_ID, "A"),
            ("A", "X"),
            (DEPOT_ID, "B"),
            ("B", "X"),
        ],
        connection_radius=100.0,
    )
    return delivery_mesh_from_parts(
        network,
        delivery_ids=["X"],
        transit_ids=["A", "B"],
    )


def _line_mesh():
    network = RoadNetwork(
        nodes={DEPOT_ID: (0.0, 0.0), "X": (10.0, 0.0)},
        edges=[(DEPOT_ID, "X")],
        connection_radius=20.0,
    )
    return delivery_mesh_from_parts(
        network,
        delivery_ids=["X"],
        transit_ids=[],
    )


class VrpDecoderEdgeReuseTests(unittest.TestCase):
    def test_outbound_and_return_use_different_paths(self) -> None:
        mesh = _diamond_mesh()
        tokens = [DeliveryToken("X", 1, priority=5)]
        plan = decode_vehicle_permutation(
            tokens,
            list(tokens),
            (0.0, 0.0),
            mesh,
            capacity=10,
        )
        self.assertEqual(len(plan.trips), 1)
        trip = plan.trips[0]
        self.assertEqual(len(trip.path_node_ids), 2)
        self.assertEqual(trip.path_node_ids[0], [DEPOT_ID, "A", "X"])
        self.assertEqual(trip.path_node_ids[1], ["X", "B", DEPOT_ID])

    def test_single_path_return_is_infinite_without_alternate(self) -> None:
        mesh = _line_mesh()
        tokens = [DeliveryToken("X", 1, priority=5)]
        plan = decode_vehicle_permutation(
            tokens,
            list(tokens),
            (0.0, 0.0),
            mesh,
            capacity=10,
        )
        self.assertEqual(plan.fitness, float("inf"))


if __name__ == "__main__":
    unittest.main()
