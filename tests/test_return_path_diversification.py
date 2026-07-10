"""Testes de retorno ao depósito com rota diferente da ida."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import (
    delivery_mesh_from_parts,
    delivery_segment_path,
)
from traveling_salesman_problem.problem.road_network import (
    RoadNetwork,
    canonical_edge,
    find_path_weighted,
)
from traveling_salesman_problem.problem.vrp_decoder import decode_vehicle_permutation
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryToken


def _diamond_network():
    return RoadNetwork(
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


class ForbiddenEdgePathfindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.network = _diamond_network()

    def test_return_uses_alternate_when_outbound_edges_forbidden(self) -> None:
        outbound = {canonical_edge(DEPOT_ID, "A"), canonical_edge("A", "X")}
        path = find_path_weighted(
            self.network, "X", DEPOT_ID, forbidden_edges=outbound
        )
        self.assertEqual(path, ["X", "B", DEPOT_ID])

    def test_forbidden_empty_matches_shortest(self) -> None:
        path = find_path_weighted(self.network, DEPOT_ID, "X")
        self.assertEqual(path, [DEPOT_ID, "A", "X"])


class MeshForbiddenSegmentTests(unittest.TestCase):
    def test_mesh_segment_respects_forbidden_edges(self) -> None:
        mesh = delivery_mesh_from_parts(
            _diamond_network(),
            delivery_ids=["X"],
            transit_ids=["A", "B"],
        )
        forbidden = {canonical_edge(DEPOT_ID, "A"), canonical_edge("A", "X")}
        path = delivery_segment_path(
            mesh,
            (20.0, 0.0),
            (0.0, 0.0),
            forbidden_edges=forbidden,
        )
        self.assertEqual(path, ["X", "B", DEPOT_ID])


class DecoderReturnDiversificationTests(unittest.TestCase):
    def test_decoder_return_differs_from_outbound_on_diamond(self) -> None:
        mesh = delivery_mesh_from_parts(
            _diamond_network(),
            delivery_ids=["X"],
            transit_ids=["A", "B"],
        )
        tokens = [DeliveryToken("X", 1, priority=5)]
        plan = decode_vehicle_permutation(
            tokens,
            list(tokens),
            (0.0, 0.0),
            mesh,
            capacity=10,
            reuse_penalty=1.75,
            return_fallback_penalty=20.0,
        )
        trip = plan.trips[0]
        self.assertEqual(trip.path_node_ids[0], [DEPOT_ID, "A", "X"])
        self.assertEqual(trip.path_node_ids[1], ["X", "B", DEPOT_ID])

    def test_decoder_single_edge_fallback_finite(self) -> None:
        network = RoadNetwork(
            nodes={DEPOT_ID: (0.0, 0.0), "X": (10.0, 0.0)},
            edges=[(DEPOT_ID, "X")],
            connection_radius=20.0,
        )
        mesh = delivery_mesh_from_parts(network, delivery_ids=["X"], transit_ids=[])
        tokens = [DeliveryToken("X", 1, priority=5)]
        plan = decode_vehicle_permutation(
            tokens,
            list(tokens),
            (0.0, 0.0),
            mesh,
            capacity=10,
            return_fallback_penalty=20.0,
        )
        self.assertTrue(plan.fitness < float("inf"))


if __name__ == "__main__":
    unittest.main()
